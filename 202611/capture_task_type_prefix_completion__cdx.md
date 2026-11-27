# Task type completion prefixes: a small, explicit writing shortcut

Researcher: **cdx** · Date: **2026-11-27**

## Assessment

**Yes: this is a good feature if it remains a small, opt-in completion convenience.** Selecting FIX in an otherwise empty capture should produce `#fix Fix `, with the caret after the final space. The task type and the task's opening verb have different roles, so their visible repetition is reasonable: the marker selects metadata, while the verb starts the description.

I recommend configuring **`capture.task_type_prefixes`** in Bryan's existing chezmoi-managed Bob configuration, applying it in **bob-cli's `capture-complete` response**, and showing the actual inserted prefix in the existing Mac task-type menu. Preserve the `types:` color map, the parser, and submission behavior.

The benefit is modest per capture but credible for a frequent gesture: the five requested words save 4–6 character keystrokes each, including the following space, with no extra selection gesture. This is a count of characters avoided, not a measured productivity result. One surprising insertion can outweigh several successful shortcuts; predictable boundaries matter more than clever inference.

This report is independent. I did not inspect another swarm researcher's report, transcript, summary, or findings. I inspected the local code and configuration, read the governing decisions through audited memory commands, consulted primary product documentation, and ran isolated CLI probes. No product implementation or personal configuration was changed.

## What the current implementation establishes

Repository snapshots inspected:

| Repository | Commit | Relevant evidence |
| --- | --- | --- |
| bob-cli | `dbdc7d24b28b2e72b2a3119155800738d4ad16ec` | Completion builder, type marker parser, config loaders, CLI tests |
| bob-mac-capture | `1eadd77ad4554d49fba56a7b10574654c8cbadb2` | Candidate decoding, menu rendering, acceptance, native editor edit helpers, hosted tests |
| chezmoi | `662569a34eb9209baa03e4cc50d32356ee2c7a08` | `home/dot_config/bob/config.yml` |

### The insertion mechanism already exists

In bob-cli, `src/native/capture_complete/task_types.rs::candidate` constructs the whole replacement string and computes `cursor_after` from its UTF-8 byte length. Leading markers currently get a space unless whitespace already follows. `TaskTypeCandidate` in `src/native/capture_complete/model.rs` carries `replacement`, `cursor_after`, type identity, styling, refusal, and the task-field effect.

The Mac's `CapturePanelModel.applySelectedCompletionReplacement` applies the supplied replacement and caret position. It does not need to synthesize `Fix` or read the configuration. This is exactly the boundary required by **`decisions:mac-capture-is-a-thin-client`**: Bob owns grammar and completion; Swift presents and applies Bob's results.

A prefix belongs in the same replacement transaction as `#fix`. Adding it with a second Swift edit would introduce unnecessary cursor, undo, and async coordination problems.

### “Leading” currently means more than “empty capture”

`capture_language/type_marker.rs` computes a leading edge through `edge_run_is_transparent`; routes and other allowed syntax can be transparent. Completion also works on later capture items. Reusing `marker.leading` alone would expand more cases than the user's example implies.

I ran the installed `bob 0.6.0` against a temporary fixture vault and explicit temporary config/cache paths, then removed the fixture. These are runtime observations of the installed binary, corroborated by source inspection; I did not rebuild it or establish that its executable corresponds exactly to the inspected commit.

| Draft and caret position | Current FIX candidate | Meaning |
| --- | --- | --- |
| `#f`, caret at end | `#fix `, caret byte 5 | Existing mechanism can produce the requested insertion |
| `  #f`, caret at end | `#fix `, caret byte 7 | Leading spaces stay outside the replacement |
| `#f `, caret immediately after `f` | `#fix`, caret byte 4 | Existing suffix whitespace is retained |
| `#f Fix parser`, caret after `f` | `#fix` | Existing description must not acquire another verb |
| `Fix parser #f`, caret at end | `#fix` | Trailing type assignment is a separate use case |
| `@dev #f`, caret at end | `#fix ` | “Leading” accepts a preceding route |
| `#f @dev:current`, caret after `f` | `#fix`, subject `existing`, effect `keep` | Type completion also edits existing-task selections |
| `First task` + blank line + `#f`, caret at end | `#fix ` | A later item also has a leading marker |
| `#fix Fix `, caret at end | No completion context | Normal typing can resume after the insertion |

The temporary config contained the five requested types; it did not contain any proposed prefix setting.

### A separate config block is the safer extension

Bryan's source file is **`chezmoi:home/dot_config/bob/config.yml`**. It already contains:

```yaml
capture:
  clipboard_history: alfred

types:
  BUILD: yellow
  CHORE: magenta
  FIX: red
  MEET: blue
  PLAN: auto
  READ: green
  WRITE: violet
```

`src/native/config/themes.rs::parse_themes_config` accepts scalar colors, `auto`, or null as type values. It rejects object values, and an invalid type block drops the configured vocabulary. An isolated probe with `types.FIX: {color: red, prefix: Fix}` returned the expected “must be … color … got mapping” warning.

Consequently, changing the shared file to object-valued `types:` entries would have a meaningful downside on older Bob installations. A new optional key within `capture:` fits the existing config shape and the independence already used for capture clipboard and template settings. See also `docs/reference/configuration.md` and `docs/task-types.md`, PT12.

### Two integration details deserve deliberate treatment

1. **Shell completion shares the builder.** `capture_complete/shell.rs` calls `task_types::build_for_shell` and turns `item.replacement.trim_end()` into shell suggestions. A change made indiscriminately inside `candidate` would also inject words into shell completion. Keep this first release scoped to editor completion deliberately.
2. **Atomic undo needs proof.** Generic Mac completion currently goes through `setPlainDraft`; record completion has a separate path using `applyNativeRewriteEdit`, and the controller has native insertion helpers with undo coalescing boundaries and expected-draft checks. The source does not justify promising that an expanded generic completion is already one native undo step. Verify with a real hosted editor test and reuse the native edit path if needed. This is a release requirement, not a claim of a confirmed existing undo bug.

## Proposed interaction contract

Describe the feature to the user as: **“Some task types can start your description when you choose them in an empty capture.”**

For FIX:

```text
Type:       #f│
Choose:     FIX  → Fix
Result:     #fix Fix │
Continue:   #fix Fix the completion spacing│
```

`│` denotes the caret and is not inserted. The word is ordinary editable text. It has no lasting link to the task type and is not a placeholder.

Expand only when all of these are true:

- The active context is Bob's `task_type` completion and the accepted candidate is enabled.
- The draft is a single physical line containing only this marker and optional surrounding horizontal whitespace.
- The caret is at the end of that marker, and acceptance is for the current draft/caret snapshot. The panel should not apply this through a noncollapsed editor selection.
- The subject is a new task.
- The selected candidate's canonical normalized type key has a valid configured prefix.

Neither highlighting a row nor merely typing or pasting `#fix` inserts text. The existing explicit acceptance gestures perform the insertion. Parsing, dry-run, capture submission, retyping an existing task, changing defaults, and reopening a stored draft do not run an expansion rule.

A manually typed `#fix ` remains available when the user wants the type without the opening word. Keep the current typing and acceptance keys; do not introduce a modifier-only bypass or a second FIX menu row.

### Required examples

| Input/context | Result after choosing FIX |
| --- | --- |
| `#f` in an empty panel | `#fix Fix ` |
| Bare `#`, explicitly choose FIX | `#fix Fix ` |
| `#fix`, explicitly choose FIX | `#fix Fix ` |
| `  #f` | `  #fix Fix ` |
| `#f   `, caret still at marker end | `#fix Fix `; normalize the completion-owned trailing gap |
| `#f Fix parser` | `#fix Fix parser`; no prefix insertion |
| `#f parser` | `#fix parser`; preserve authored text even though it lacks a verb |
| `Fix parser #f` | `Fix parser #fix` |
| `@dev #f` | Normal current type completion; no prefix |
| `#f @dev` | Normal current type completion; no prefix |
| `#f @dev:current` | Normal existing-task type completion; no prefix |
| A second capture item or a child bullet | Normal current completion; no prefix |
| A heading, drawer, Pomodoro name, or reserved clock tag using `#` | Its own existing behavior; never this feature |
| Choose an unconfigured-prefix type such as CHORE | Normal type-only completion |

For the five requested configured entries, the exact outputs are `#fix Fix `, `#build Build `, `#plan Plan `, `#read Read `, and `#write Write `.

### Requirement adjustments, explicitly called out

**A. Clarify “start” as a fresh single-line draft, not every semantic leading edge.** This deliberately excludes route-first captures, later items, and markers inserted before an existing description. It matches the empty-panel example and makes the first release easy to explain and trust. If frequent use demonstrates that route-first capture needs the shortcut, widen the predicate explicitly using Bob's parsed new-task context; do not silently broaden it through the existing `leading` flag.

**B. Add a preview and atomic undo as acceptance criteria.** They were not explicit in the request, but they make an otherwise surprising side effect visible and reversible. One Command-Z should restore the pre-accept draft and caret; Redo should restore the expanded draft. Subsequent typing should remain a separate undo group. Ordinary Backspace retains its normal character deletion behavior.

**C. Keep the feature out of automatic text rewriting and shell completion initially.** The request names selection from the capture panel. This boundary prevents unrelated capture callers from gaining hidden behavior and keeps shell quoting outside the initial scope. `capture-complete` remains reusable by another editor client that chooses to apply the same Bob-authored replacements.

**D. Store literal prefixes, rather than infer title case from every type name.** The five mappings are personal configuration, with no global built-in enablement. Future names such as CHORE or MEET may not make natural opening verbs; even READ may sometimes introduce a task whose desired wording starts differently.

## Configuration and validation

Add to the existing `capture:` mapping, preserving `clipboard_history` and the existing `types:` map:

```yaml
capture:
  clipboard_history: alfred
  task_type_prefixes:
    FIX: Fix
    BUILD: Build
    PLAN: Plan
    READ: Read
    WRITE: Write
```

The key names are proposed here, not existing supported settings. Omitting the map or using `{}` disables all prefixes. Deleting an entry disables that type. There is no additional enable flag or default title-casing mode.

Suggested rules:

- Normalize keys with Bob's existing type identity function, not selector slug formatting; use uppercase names in documentation and Bryan's config. Reject normalized duplicates such as `FIX` and `fix` instead of picking an arbitrary winner.
- Values are nonblank strings containing plain, single-line description text. Trim outer whitespace; the renderer owns separators. Short phrases such as `Follow up on` can fit the same model without adding variables, tab stops, or snippet syntax.
- Reject line breaks/control characters and values that the existing capture parser would interpret as additional capture syntax. Validate against the shared parser with a synthetic type-plus-prefix draft; require exactly one ordinary new task with the expected description and unchanged marker meaning. Avoid a second, frontend-maintained sigil blacklist.
- Never execute commands or perform interpolation. A prefix is text, not a template program.
- A map entry must not add a candidate, change ranking, revive hidden types, or bypass a refusal. Match only against an independently offered and accepted type. In a configured vocabulary, unmatched map keys should be diagnosed as likely stale config; without one, they may match independently offered history types.
- Missing configuration means ordinary completion. Invalid optional prefix configuration should produce a bounded warning and fall back to type-only completion, preserving valid type colors and other capture settings. For a malformed map or normalized-key collision, disable that map; for an isolated invalid value, identify and ignore that entry. Be explicit in diagnostics and tests about this distinction.

Load this setting through Bob's ordinary config-path precedence (`BOB_CONFIG_FILE`, XDG, then the home config). Swift never reads chezmoi or YAML. Parse or share a configuration snapshot once per completion request rather than once per candidate. Existing per-request process execution makes a separate persistent prefix cache unnecessary.

There is a small maintenance cost to a separate map: a type rename may require a corresponding config edit. Bob already treats the user-owned type vocabulary as read-only. Document the companion key and diagnose stale entries; do not add automatic chezmoi mutations.

## API, editor, and visual design

The operative change for an eligible FIX row is simply:

```json
{
  "replacement": "#fix Fix ",
  "cursor_after": 9,
  "name": "FIX",
  "key": "fix",
  "body_prefix": "Fix"
}
```

This is an illustrative fragment, not a complete response. **`body_prefix` is proposed optional presentation metadata**, emitted only when this row actually inserts the prefix in this context. The existing `effect` remains the task-field effect (`set`, `clear`, or `keep`); do not repurpose it to describe text expansion. A new task whose type is inherited can still get its configured opening word even when the effect is `keep`.

Bob owns the complete replacement and cursor. Swift uses `body_prefix` to render and announce the consequence, never to reconstruct the inserted text. Existing clients can apply the expanded replacement even if they ignore the new metadata; a new client talking to an older Bob simply receives no hint or expansion. This should remain an additive schema-1 response extension, subject to fixture checks, rather than a grammar revision.

Whitespace requires care because the response currently carries one common replacement range. For an eligible otherwise-empty draft, include trailing horizontal whitespace in that common range and build **all** candidates against the same range, each yielding one appropriate trailing separator. Preserve leading whitespace outside the range. Do not widen the range only for FIX while leaving another candidate's cursor calculation based on the old span. Never consume a newline or authored suffix.

Caret values stay UTF-8 byte offsets, including for non-ASCII prefixes and text before the marker. Swift should continue using its existing validated byte-to-string/UTF-16 conversions; character counts are not interchangeable with byte counts.

### Make the existing menu slightly more informative

`CaptureTaskTypeMenuView` already has colored type pills, usage captions, fixed-height rows, selection styling, and accessibility labels. Preserve that visual language and row height. Add a secondary **`→ Fix`** consequence next to the FIX pill only for eligible rows. The currently selected footer can say **“Start with ‘Fix’”** while retaining existing acceptance hints. At narrow widths, prioritize the consequence over usage history; keep the full consequence available to accessibility.

Example row, schematically:

```text
[red swatch] [FIX]   → Fix                        usage
```

Use the existing semantic secondary text style with readable contrast. Do not introduce another color, animated insertion, transient toast, ghost text layer, or extra confirmation. The editor retains normal syntax tint for `#fix`; `Fix` appears as ordinary prose immediately after acceptance. VoiceOver should communicate “FIX; starts the description with Fix” rather than relying on the arrow or color.

The specialized task-type view and presentation model need the hint; changing only generic `CompletionRowContent` would miss that menu. The generic representation should receive an equivalent accessibility consequence where used.

### Reliability requirements

Bind acceptance to the exact current draft and caret snapshot. A response generated for `#f` must not insert `Fix` after the user has already typed a description or moved the caret. Extend and test existing cancellation/snapshot handling rather than starting an independent prefix timer. If a config edit happens while a menu is open, accept the replacement displayed by that snapshot or refresh the menu; do not recompute a different hidden insertion on click.

Use one native undoable edit for the full replacement and caret move. The Mac's existing expected-draft native edit machinery is a promising reuse point. After acceptance, reschedule normal parse/preview without automatically reopening the same menu. Deleting or editing the inserted word does not cause it to be replenished.

## Alternatives and critique

| Approach | Merit | Why I would not choose it here |
| --- | --- | --- |
| Automatically capitalize and repeat every type | Minimal config | Type categories are not consistently useful verbs; lacks per-type control |
| Expand whenever `#fix` is typed or on submit | Works outside the menu | Changes literal text and scripted capture behavior; easier to trigger accidentally |
| Infer FIX when prose starts with “Fix” | Removes more typing | Inverts metadata authority and can classify prose incorrectly; a separate product decision |
| Add a new snippet trigger or saved template | Suitable for longer structured captures | Adds a new convention or selection step for a five-word shortcut |
| Use macOS text replacement | Already a familiar convenience | A generic replacement table lacks Bob's parsed task-type and new-task context; does not satisfy chezmoi ownership as naturally |
| Extend `types.FIX` to `{color, prefix}` | Co-locates type metadata | Current readers reject object values and drop the vocabulary; unjustified migration risk for this feature |
| Insert the word from Swift after choosing a type | Small-looking frontend patch | Duplicates semantics, splits the edit, and violates the thin-client decision |

Completion-driven snippets are a familiar precedent: VS Code allows snippets to appear among completion suggestions and be inserted by an explicit acceptance gesture. My inference is that Bob can use the same basic interaction while requiring only literal text, with none of that editor's richer snippet machinery. This is a precedent, not evidence that this particular Bob feature improves throughput. [VS Code snippet documentation](https://code.visualstudio.com/docs/editing/userdefinedsnippets)

Apple documents configurable text substitutions as a typing convenience. That supports the general concept, but its generic replacement model does not establish Bob's required contextual behavior. I used the official search excerpt; opening the page was rate-limited during this research. [Apple text replacement documentation](https://support.apple.com/guide/mac-help/replace-text-punctuation-documents-mac-mh35735/mac)

The main risk is not implementation complexity; it is a subtle change in the meaning of “choose a type.” The visible consequence, narrow trigger, personal opt-in, and one-step undo address that risk directly. If everyday use involves frequent deletion of these words, remove individual mappings rather than adding heuristics. A lightweight manual trial is sufficient; this does not warrant telemetry infrastructure.

## Implementation boundaries and verification

This is research guidance, not an implementation or a SASE plan.

**bob-cli:** add an independent capture-prefix config loader; decorate eligible editor task-type candidates after ordinary catalog/refusal resolution; return optional display metadata; coordinate the common range and caret offsets. Keep `build_for_shell` explicitly type-only. Likely files are `src/native/config/capture.rs`, `config/mod.rs`, `capture_complete/task_types.rs`, `capture_complete/model.rs`, and the task-type branch in `capture_complete/engine.rs`.

**Mac:** decode optional metadata in `Sources/CaptureCore/CaptureModels.swift`; carry it through `CaptureTaskTypeMenuPresentation`; render it in `CaptureTaskTypeMenuView`; verify acceptance and, if necessary, route the splice through native undo machinery. Do not port eligibility logic or YAML parsing to Swift.

**chezmoi:** add the five entries to `home/dot_config/bob/config.yml` after implementation is available. Follow that repo's required apply workflow after its eventual commit. No Obsidian plugin change appears necessary for this panel-scoped feature.

**Documentation:** explain the fresh-draft boundary and the type-only typing path in capture docs; add the config reference and optional response field. Before changing those files, follow the repository's docs-memory workflow.

Focused verification should cover:

1. All five exact requested expansions, bare-hash explicit selection, fully typed marker acceptance, and an unmapped type.
2. Every no-expansion case in the table, including routed drafts, existing tasks, later items, and other meanings of `#`; preserve reserved clock-tag behavior from `decisions:capture-reserves-clock-tags`.
3. The no-config path, malformed map, invalid scalar, normalized duplicate keys, stale names, and independent survival of valid colors and clipboard settings.
4. Leading/trailing whitespace, Unicode prefix byte counts, complete-token replacement, and agreement of every candidate with the common range.
5. Shell completion regression fixtures: no injected word.
6. New/old client compatibility and exact parser round-trip: expanded bytes still represent the intended type and ordinary body, with no new grammar behavior.
7. Hosted Mac acceptance by keyboard and mouse; one-step undo/redo; ordinary typing afterward; deletion without re-expansion; delayed response after typing/caret movement; menu accessibility and narrow-width presentation.

Extend existing suites such as `tests/cli/capture/complete_task_types.rs`, `tests/cli/completion/capture_text.rs`, `CaptureTaskTypeTests`, and `CaptureTaskTypeHostedTests`. Pure model assertions are insufficient to establish native undo behavior.

No Swift build or hosted UI test was run for this research-only deliverable. The eventual implementation must compile changed Swift and run the Mac repository's required portable and macOS verification, including its exact-SHA CI gate. For bob-cli, respect **`decisions:bob-cli-releases-ride-a-daily-train`**: no manual version or changelog edits; contract breaks, if any become necessary, must be marked explicitly. Ship compatible CLI/client support before enabling Bryan's mappings so his first experience includes the explanatory hint.

## Source index and governing decisions

Local source citations refer to the repository snapshots above, not to other researchers' reports:

- **Completion semantics:** bob-cli `src/native/capture_complete/task_types.rs` (`build`, `build_for_shell`, `candidate`); `model.rs::TaskTypeCandidate`; `engine.rs` task-type branch; `shell.rs` task-type branch.
- **Marker boundaries and spelling:** bob-cli `src/native/capture_language/type_marker.rs` (`scan_line_with_positions`, `completion_at`, `replacement_for`, `edge_run_is_transparent`); `capture_language/completion.rs` task-type context.
- **Configuration:** bob-cli `src/native/config/themes.rs`, `config/capture.rs`; `docs/task-types.md` PT12; `docs/reference/configuration.md`; chezmoi `home/dot_config/bob/config.yml`, existing capture block around line 212 and types block around line 260.
- **Mac interaction:** `Sources/BobMacCapture/CapturePanelModel.swift` (`acceptSelectedCompletion`, `applySelectedCompletionReplacement`, `setPlainDraft`, `applyRecordDraftEdit`); `CapturePanelController.swift::applyNativeRewriteToDraftEditor`; `CaptureTaskTypeMenuView.swift`; `Sources/CaptureCore/CaptureTaskTypeMenuPresentation.swift`, `CaptureModels.swift`, and `CompletionRowContent.swift`.
- **Existing tests:** bob-cli `tests/cli/capture/complete_task_types.rs`; Mac `Tests/CaptureCoreTests/CaptureTaskTypeTests.swift`, `Tests/BobMacCaptureTests/CaptureTaskTypeHostedTests.swift`, and task-type JSON fixtures.
- **Audited memory:** `decisions:mac-capture-is-a-thin-client`, `decisions:capture-sigils-say-where-what-how`, `decisions:capture-reserves-clock-tags`, `decisions:bob-cli-releases-ride-a-daily-train`; glossary definitions for Capture, Capture Panel, and Task Type.

## Recommended solution

Implement **opt-in task description prefixes** under `capture.task_type_prefixes`, configured in chezmoi for FIX, BUILD, PLAN, READ, and WRITE. Have Bob return `#fix Fix ` as one ordinary completion replacement only in an otherwise-empty single-line draft; keep typing, parsing, submission, existing-task edits, and shell completion unchanged. Show **`FIX → Fix`** in the existing menu, preserve the type's color and ranking, and require atomic native undo and stale-response tests before shipping. This meets the requested shortcut with a small, inspectable rule and leaves room to expand its scope only if actual use warrants it.
