# Canonical #off / #on tags and inherited task clock policy

Independent research by **cdx**, 2026-11-02.

**Assessment.** This is a good extension of Bob’s clock model. A stable area default removes repeated tagging, and `#on` gives a useful exception for work that happens inside an otherwise personal area. Keep the requested `offclock: true|false` field and short tags. Implement them as task policy resolved at the time a session is written, while retaining the existing recorded session clocks. This is a coordinated bob-cli and Obsidian change, with a separate historical spelling migration; it is larger than a Google token-parser change.

The most consequential adjustment is to replace “always offclock” with **“off-clock by default, subject to explicit task overrides and the session’s existing counted-links rule.”** A session linking a love task and a worked task still counts entirely as Worked. This preserves the behavior established by `bob-cli-fl`, rather than introducing unmeasured per-task time allocation.

This report is research, not implementation. I inspected source, tests, the epic, and its approved plan; I did not modify the vault, migrate tasks, change product code, or execute the test suites. I did not inspect any other report or findings from this swarm. Live vault counts, existing uses of `#on`/`#off`, and the current contents of `love.md` remain deployment checks rather than measured facts.

**Evidence and the current baseline.**

The inspected revisions were bob-cli `1562baab267edf7663a178972e96c15baa583671`, bob-plugins `e9f2fb71019fbaa4a78579339c0c4b995f681218`, and bob-mac-capture `1b61ac762f3cfddb30ab61742117431902ffbaab`. The audited `bob-cli-fl` bead read reported the epic in progress: its CLI, settlement, plugin clock-writer, and Mac phases were closed; its plugin Stats phase was still in progress. Recheck that state before implementation rather than assuming the epic has finished.

| Finding | Source inspected |
| --- | --- |
| A session is Off-clock only when its retained Task Link set is nonempty and every link resolves to an off-clock task. Empty, unresolved, and mixed lineups are Worked. | [event_task.rs: LinkFact, clock_verdict](https://github.com/bobs-org/bob-cli/blob/1562baab267edf7663a178972e96c15baa583671/src/native/event_task.rs); audited `plan:202611/off_clock_pomodoros.md` |
| Current tag spellings are `#offclock`, `#off-clock`, and `#untracked`, case insensitive. The Markdown parser excludes inline code and Markdown links and rejects nested tag suffixes. | [event_task.rs: line_has_off_clock_tag](https://github.com/bobs-org/bob-cli/blob/1562baab267edf7663a178972e96c15baa583671/src/native/event_task.rs) |
| Google parsing reduces explicit clock intent to booleans. Titles remove accepted tokens; descriptions recognize whole directive-only lines after HTML normalization. | [gcal/model.rs](https://github.com/bobs-org/bob-cli/blob/1562baab267edf7663a178972e96c15baa583671/src/native/gcal/model.rs) |
| Rendering and lifecycle parsing place clock tags in the Google-owned badge span. Sync compares hashes to preserve edits and protects clock flips on touched/worked rows. | [gcal/render.rs](https://github.com/bobs-org/bob-cli/blob/1562baab267edf7663a178972e96c15baa583671/src/native/gcal/render.rs), [gcal/lifecycle.rs](https://github.com/bobs-org/bob-cli/blob/1562baab267edf7663a178972e96c15baa583671/src/native/gcal/lifecycle.rs), [gcal/plan.rs: apply_span_updates](https://github.com/bobs-org/bob-cli/blob/1562baab267edf7663a178972e96c15baa583671/src/native/gcal/plan.rs) |
| There is already a cached note-facts and parent-chain abstraction, with disk and indexed sources and shared note-link resolution. It distinguishes a full residence chain from the reporting root. | [pomodoro_homes/facts.rs](https://github.com/bobs-org/bob-cli/blob/1562baab267edf7663a178972e96c15baa583671/src/native/pomodoro_homes/facts.rs), [pomodoro_homes/resolve.rs](https://github.com/bobs-org/bob-cli/blob/1562baab267edf7663a178972e96c15baa583671/src/native/pomodoro_homes/resolve.rs) |
| Stats reads stored session clocks; current task classification is also used to diagnose drift. | [stats/homes.rs: ClockTaskLookup, session_drifted](https://github.com/bobs-org/bob-cli/blob/1562baab267edf7663a178972e96c15baa583671/src/native/stats/homes.rs), [stats_clock.rs: writer_stamped_off_clock_row_agrees_with_stats_until_the_task_drifts](https://github.com/bobs-org/bob-cli/blob/1562baab267edf7663a178972e96c15baa583671/tests/cli/stats_clock.rs) |
| Reconcile automatically completes eligible ended off-clock Event Tasks and records closed off-clock sessions. | [task_status_hooks/settle.rs](https://github.com/bobs-org/bob-cli/blob/1562baab267edf7663a178972e96c15baa583671/src/native/task_status_hooks/settle.rs) |
| Obsidian has separate JavaScript implementations for starts, closes, and Event Task presentation. | [ledger-tools clock model](https://github.com/bobs-org/bob-plugins/blob/e9f2fb71019fbaa4a78579339c0c4b995f681218/plugins/bob-ledger-tools/src/036-pomodoro-clock.js), [cycler clock model](https://github.com/bobs-org/bob-plugins/blob/e9f2fb71019fbaa4a78579339c0c4b995f681218/plugins/task-status-cycler/src/062-pomodoro-clock.js), [Event painter](https://github.com/bobs-org/bob-plugins/blob/e9f2fb71019fbaa4a78579339c0c4b995f681218/plugins/bob-ledger-tools/src/291-plugin-gcal-events.js) |

I also read the relevant decision records through `sase memory read`: off-clock clocks, event settlement, Google read-only ownership, Google root updates, and the Mac thin-client rule; and the area, project, root-parent, Event Task, Task Link, and Off-Clock Pomodoro glossary definitions. The clock decision explicitly lists area-based policy as a condition for reopening the original tag-only choice. The proposed change therefore has a natural architectural place, but the old “task’s own line must carry a tag” contract must not silently remain the specification.

**Recommended semantics.**

Use three authored states: **inherit**, **off**, and **on**. Absence is not `false`.

| Input, in precedence order | Effective task clock |
| --- | --- |
| Task has standalone `#on` | Worked |
| Otherwise task has `#off` or an accepted legacy alias | Off-clock |
| Otherwise nearest applicable area/project has `offclock: true` | Off-clock |
| Otherwise nearest applicable area/project has `offclock: false` | Worked; this ends inheritance from higher ancestors |
| Otherwise no applicable setting is found | Worked |

A deeper descendant may set `true` again below a `false` parent. Neither a project’s `root: true` nor a reporting root boundary stops this walk. A task’s own explicit `#off` still wins over a note’s `offclock: false`. Tags on a containing task, Task Link, dependency, heading, or prose paragraph do not become implicit overrides for other tasks.

**Adjustment: contradictory tags.** If the same task or Google event contains `#on` and an off spelling, choose Worked and report a conflict. Give `#on` precedence across the accepted Google title and description directives, rather than making source order decisive. This is deterministic, preserves the explicit escape hatch, and errs toward the existing Worked fallback. It should not abort unrelated event sync. Writers should emit only the winning canonical tag; a migration should flag contradictory existing rows for review rather than silently deleting user intent.

**Adjustment: strict field values.** Require actual boolean `true` or `false`; missing means inherit. Treat null, blank, quoted strings, numbers, lists, and duplicate keys as invalid and diagnose them. Do not use JavaScript truthiness: the string `"false"` must never enable off-clock behavior. For an invalid nearer setting, stop and fall back to Worked with a warning rather than unexpectedly inheriting `true` from above. Explicit task tags still decide before a broken note default is needed. Shared fixtures must define this behavior identically for the Rust frontmatter parser and Obsidian’s typed frontmatter.

For unresolved/ambiguous parent links, a cycle, or a traversal limit reached before finding a setting, use Worked and a bounded diagnostic. A valid nearer boolean already decides the task without needing the rest of the chain. The existing homes walk has a depth limit of 16; do not silently turn that implementation detail into “recursive inheritance works only for the first 16 notes.” Prefer a cycle-safe iterative walk, or document and diagnose a defensive cap.

**Which note supplies the policy?**

The word “belonging” needs a contract. I recommend:

- Ordinary tasks begin at their containing area/project note and follow `parent` links.
- Daily Event Tasks begin at the note named by their current valid `[root::]` field, because their physical residence is the daily note. If no usable root exists, explicit task tags still work; otherwise default to Worked and diagnose invalid roots.
- Reference/archive wrapper notes may walk through their established parent provenance to an area/project. Only area/project notes contribute `offclock` values; do not let a year folder, daily-note template, or generic wrapper become a global clock policy.
- Use exact resolved note identities and existing ambiguity checks. Folder location, note-name prefixes, colors, and theme names are not ancestry.

This intentionally preserves the glossary’s distinction between residence and reporting. **Adjustment: an ordinary task’s reporting-only `[root:: love]` should not silently change its clock.** If you want that attribution override to become a policy override for all task kinds, make it a separate explicit requirement. For this change, the Event Task exception is both necessary and sufficient.

Do not begin inheritance at the *collapsed reporting root*. That loses intermediate project overrides. Start at the event’s actual root target or the ordinary task’s resident note, then walk upward. If Google routing cannot select some subproject today, do not expand routing rules incidentally; inheritance can still apply to tasks in that subproject and to any supported event root target.

Example intended behavior after adding `offclock: true` to `love.md`:

| Task | Result |
| --- | --- |
| Untagged ordinary task in love | Off-clock |
| Untagged task in a child project of love | Off-clock |
| Child project has `offclock: false` | Its untagged tasks are Worked |
| Grandchild restores `offclock: true` | Its untagged tasks are Off-clock |
| `#on` task anywhere below love | Worked |
| `#off` task inside the false child | Off-clock |
| Daily Event Task with `[root:: love]` and no clock tag | Off-clock |
| That Event Task has `#on` | Worked |
| Ordinary job task has reporting-only `[root:: love]` | Follows job’s clock policy |
| Session retains love task plus a Worked task | Whole session is Worked |

**Separate explicit intent from effective classification.**

The most important implementation choice is to avoid materializing inheritance into task tags. If sync writes `#off` merely because `love.md` is true, that derived value becomes indistinguishable from an explicit user override. Removing the area setting, setting a child false, moving the task, or rerouting the event would then leave it incorrectly pinned off-clock.

Represent these concepts separately, for example:

```text
ClockOverride = Inherit | On | Off
ClockResolution = { off_clock, source, source_note?, diagnostics }
```

The actual type names are implementation choices. Preserve “none” through parsing; do not replace it immediately with `false`. Retain the deprecated spellings encountered as parser diagnostics so later code can emit warnings even when `#on` wins.

Canonical Google output should render:

- Explicit Google off directive → `#off`.
- Explicit Google on directive → `#on`.
- No Google directive → no authored clock tag, even when inheritance makes the task off-clock.

Rendered tags describe explicit input; JSON `off_clock` describes effective behavior. Continue using `off_clock` and existing compatibility fields in the JSON contract. The spelling change does not justify renaming JSON keys, the `[off::]` ledger field, the Stats clock values, or the display term “Off-clock.”

Resolve against the final planned vault state. For an existing synced event, preserve any vault-owned edits under the current ownership rules, determine the resulting root, and then compute effective clock policy. Using Google’s proposed root before the merge can classify an event under love while its retained vault root points somewhere else. For capture batches, staged changes and the live editor buffer must take precedence over disk snapshots.

The existing separation between a syntax parser and a contextual resolver should become explicit. `events_in_note` and `event_task_by_id` currently produce tag-derived booleans without parent context; extending only `line_has_off_clock_tag` cannot implement inheritance. Parse the row first, then resolve policy using the note/vault context.

**Google behavior and deprecation warnings.**

Keep the current directive grammar. Recognize exact standalone `#off` and `#on` tokens case insensitively in titles and on description directive-only lines. Preserve current punctuation behavior and normalization; do not expand arbitrary prose scanning as part of this change. `#office`, `#online`, `#off/foo`, and tag-like URL fragments must not qualify. Test title routing after clock-token removal, especially `Lunch @love #on`.

Google explicitly permits HTML in event descriptions, which supports retaining Bob’s existing normalization before tokenization. This is a Bob convention over event text, not a native Calendar off-clock property. [Google Events resource](https://developers.google.com/workspace/calendar/api/v3/reference/events)

**Adjustment: keep and deprecate all three aliases**, including the previously accepted `#off-clock`, rather than accidentally dropping it. Deprecation means “prefer `#off` for new input,” not a scheduled removal. The earlier epic calls the aliases permanent; warnings can change without breaking their continued meaning.

Recommended warning contract:

- Emit one actionable warning per affected occurrence per invocation, listing the distinct deprecated spellings seen and the replacement.
- Produce it whether the vault row is newly written or unchanged, and in dry-run results. Derive it from parsed Google input, not from a text diff.
- Aggregate duplicate title/description mentions. If both polarities occur, report that conflict as well.
- Keep ordinary human warnings on stderr; keep JSON stdout valid, with the same warning in its existing `warnings` array. Do not change that array from strings to objects incidentally.
- Preserve the existing `--quiet` success-output contract; JSON/status reporting can retain warnings. No persistent “warned once forever” journal is needed.
- Include enough event identity to find the offending input, but do not copy entire descriptions into logs.

For example: `warning: Lunch: #untracked is deprecated; use #off. The event remains off-clock.` When `#on` wins, the message must say so rather than claiming off-clock behavior.

Keep Google read-only. The requested backfill is for Obsidian Event Tasks, not remote Calendar event text. Continue warning on old recurring-series input until Bryan edits it in Calendar. No new OAuth permission is necessary; Google distinguishes its read-only scope from event-write scopes. [Google Calendar scopes](https://developers.google.com/workspace/calendar/api/auth)

**Code surfaces that must agree.**

| Surface | Required change |
| --- | --- |
| Shared Rust clock policy | Add explicit override parsing and contextual resolution; reuse note/link infrastructure; preserve `clock_verdict` itself |
| `gcal/model.rs`, `render.rs`, `lifecycle.rs`, `plan.rs`, `sync.rs`, `list.rs` | Parse both polarities and aliases; render explicit canonical tags; resolve effective policy after routing/merge; warn; keep list/sync fields truthful |
| `capture_pomodoro_start.rs`, `capture/meet_event_run.rs` | Resolve each counted task through policy, including same-note events and staged capture data; split event runs by effective clock |
| `capture_pomodoro_close/linked_tasks.rs` | Resolve the final retained links after selection, carrying, and deferral; stamp the final clock |
| `task_status_hooks/settle.rs` and its callers | Supply contextual policy; inherited off-clock Event Tasks must be eligible just like explicitly tagged ones |
| `capture_pomodoros.rs`, event conflicts, agenda/preview | Show effective classification even where there is no visible `#off` tag |
| `stats/homes.rs` | Use the shared policy for drift diagnostics, while keeping stored session keys authoritative for totals |
| Obsidian ledger-tools `035-meet-event-run.js`, `036-pomodoro-clock.js`, Event painter, and related start integration | Resolve contextual task policy, not just a line regex; mark inherited off-clock events in editor and Reading view |
| Obsidian task-status-cycler `062-pomodoro-clock.js` and close integration | Return task identity/context as well as line text so closes can resolve ancestors |
| Mac capture | Consume effective booleans from bob; no Swift inheritance engine |

A shared Rust service with a source abstraction is the best fit. Reuse `HomeSource`/note-fact caching and `VaultLinkResolver` patterns without forcing clock semantics into the reporting-root function. Cache resolutions per command or snapshot, not indefinitely across note edits. Parent and offclock edits, moves, renames, and new ambiguity must invalidate affected results.

For Obsidian, keep one pure policy contract and copy or generate its JavaScript implementation into the standalone plugins through their established build system, with shared vectors owned by bob-cli. The current plugins intentionally do not import one another. Replacing all editor mutations with subprocess calls could be a future architecture project, but it is unnecessary scope here and complicates unsaved editor state. Avoid adding yet another unrelated local rule inside the Event painter.

The Mac already refreshes its agenda on visible Markdown changes, so `love.md` edits appear covered by its existing relevance filter; confirm with a test rather than adding a new watcher. [CaptureAgendaRefreshFilter.swift](https://github.com/bobs-org/bob-mac-capture/blob/1b61ac762f3cfddb30ab61742117431902ffbaab/Sources/CaptureCore/CaptureAgendaRefreshFilter.swift)

**Historical migration needs its own operation.**

Do not rely on repeatedly running daily `gcal sync` or on a global search-and-replace. Daily sync cannot guarantee coverage of all historical rows, and it intentionally protects edited rows. A text-wide replacement would also alter prose, code examples, URLs, nested tags, and other inert occurrences.

Provide a previewable, repeatable vault migration that replaces recognized legacy tag token spans with `#off` in task rows, including completed and canceled Event Tasks in old daily notes and archived task copies. **Adjustment: normalize legacy tags on other actual task rows too**, because the request also adopts `#off` throughout Obsidian. Do not use the normal open-task filter or exclude `done/`. Do not edit Git history, remote Calendar data, generated assets, reference source stores, or conflict copies as part of this operation.

Preserve every unrelated byte where possible: status, title, timestamps, root/type/buffer fields, children, block IDs, Task Links, line endings, and session rows. Retain an explicit `#off` even if the current parent already supplies true; deleting it would change what happens after a later move or override.

The migration’s critical complication is the Calendar journal:

1. Before editing a managed row, compute its old span hashes and compare them to the recorded baseline.
2. If a changed span was genuinely untouched, append a new baseline for its canonicalized form. Check both title and badge spans: older rows may contain the old tag in the title. An existing lifecycle test already covers migration of a title token across spans.
3. If the span already differs from the journal, canonicalize only the authorized token bytes while preserving the fact that the span was user-edited. Never set the entire modified badge/title span as the new Google-owned baseline.
4. Preserve tombstones, occurrence identity, manual roots, and unrelated journal state. Append journal updates through its API; do not rewrite old journal history.
5. Record enough transaction evidence to recover if notes are written but journal append fails. Current normal sync writes the note before appending the journal, so a vault-wide migration must explicitly address that crash window.

See [gcal_lifecycle.rs: preexisting_off_clock_title_migrates_both_spans_in_place](https://github.com/bobs-org/bob-cli/blob/1562baab267edf7663a178972e96c15baa583671/tests/gcal_lifecycle.rs) and [gcal/sync.rs](https://github.com/bobs-org/bob-cli/blob/1562baab267edf7663a178972e96c15baa583671/src/native/gcal/sync.rs). Alias-equivalent hashing is another possible design, but it also needs a compatibility bridge for existing raw hashes. Explicit migration baseline repair is easier to audit than changing every ownership comparison.

Use the existing maintenance lock, snapshot/recheck, atomic-file, validation, and reversible-commit patterns from [types migration](https://github.com/bobs-org/bob-cli/blob/1562baab267edf7663a178972e96c15baa583671/src/native/pomodoro_themes/migrate.rs). Reuse its safety machinery, not its scope: it deliberately excludes closed tasks and `done/`, which would violate this request. A proposed `bob task migrate-clock-tags` command fits the existing rule that `bob task` verbs rewrite task lines across the vault; that command does not currently exist. Design its preview/apply interface under the project’s CLI conventions.

The preview should report changed files/rows, token counts by spelling, contradictory rows, unresolved managed-row bookkeeping, and remaining eligible legacy tokens. Run twice to prove idempotence. A successful migration must not silently skip past Event Tasks and still claim completion.

**Historical time and settlement are different concerns.**

A spelling migration is semantics-preserving. Adding a parent policy is a change to future classification. Keep those as separate changes and separate verification steps.

Do not rewrite closed `[t::]` sessions to `[off::]`, restamp bare historical spans, or synthesize years of love sessions. Existing closed clocks remain authoritative. A past Worked love session may now show policy drift; label that as a difference from current policy, not evidence that its original recording was wrong. Alias-only normalization should produce no additional drift.

Running sessions can be reclassified when the next supported start/link/close operation recomputes their retained lineup, following the existing writer rule. At minimum close must resolve current policy. Do not add a background process that rewrites closed sessions in response to frontmatter changes.

The largest behavioral consequence is **automatic settlement**. Once love supplies an inherited off-clock default, an ended, open love Event Task still queued under an eligible untimed MEET can be automatically recorded and completed by reconcile, even if Bryan never started it. This follows the current accepted settlement policy, which already acknowledges that calendar presence is not proof of attendance.

I would keep that policy for this change, rather than introducing a second `autosettle` property. But activation should preview today’s newly eligible events, and the report/help should explain that canceling an event before it ends prevents this inference. Ordinary off-clock tasks do not become auto-completable just because their area is true.

**Alternatives and critique.**

| Alternative | Assessment |
| --- | --- |
| Rename tags only | Useful small first release, but fails the requested inheritance and still requires repetitive tags |
| Write `#off` onto every descendant task | Reject: derived values become sticky explicit overrides; moves and false children stop behaving naturally |
| Infer all sessions from today’s hierarchy when reading Stats | Reject: changing a parent silently rewrites the meaning of historical time |
| Use `clock: off|on` frontmatter instead | A coherent enum, but no present third clock mode needs it. The requested boolean with absence-as-inherit is sufficient; avoid another naming migration |
| Honor every task’s `[root::]` for inheritance | Simpler conceptual reuse, but broadens a reporting-only field into behavior. Use the Event Task exception unless this extra change is deliberately chosen |
| Move Google directives into private extended properties | Adds write/API/UI requirements without solving the Obsidian hierarchy problem; keep the existing read-only text convention |
| Split a mixed session by linked tasks | Requires per-task time evidence. Equal splitting would invent precision; keep the whole-session rule |
| Implement inheritance independently in each consumer | Highest drift risk. Use one policy specification, shared fixtures, and contextual adapters |

Short tags are convenient but generic. Before enabling them, inventory existing active `#off` and `#on` task uses and Google inputs for collisions. That is a concrete activation check, not a reason to prefer a longer spelling automatically. Keep UI wording explicit—“Off-clock · inherited from love”—because `#off` alone has weak meaning outside its context.

There is also a measurement tradeoff: “Worked” now reflects a configurable boundary, not a moral distinction between valuable and unimportant time. A difficult family project might appropriately use `#on` or a false child default. The override mechanisms make that choice practical without renaming the established clocks.

**Implementation sequence and proof obligations.**

1. Rebase against the finished `bob-cli-fl` work and pin the source/vector revisions used. Establish the semantics above before changing writers.
2. Add the explicit-override model and the contextual resolver. Add canonical/legacy parsing and Google warnings. Keep recorded session formats unchanged.
3. Thread the resolver through every CLI writer and reader listed above, including settlement and drift. Ensure root merges precede effective resolution.
4. Update both Obsidian writer implementations, event visuals, unsaved-buffer handling, and cache invalidation; rebuild generated entrypoints and run the repo’s required checks. Verify the Mac remains a thin consumer.
5. Ship compatible readers and writers to all active hosts before switching emitted task spelling or activating frontmatter. If separate rollout makes this difficult, stage alias recognition first, then canonical output/inheritance. Older plugins can misclassify both unrecognized `#off` and untagged inherited tasks.
6. Preview and apply the historical spelling migration on the designated vault writer, with other writers coordinated through the established maintenance mechanisms.
7. Preview the love-policy impact and add the single `offclock: true` field to the existing `love.md`, preserving its other frontmatter. Activate the deployed behavior and verify actual start, close, and settlement results.

The code release must follow Bob’s normal daily train. A subsequent implementation plan also needs to address the accepted tag-only clock decision and affected glossary contracts through the SASE memory authorization workflow; this research creates no memory changes or new memory authorization.

Use source-backed fixtures and behavior tests, not just matching regex unit tests:

- **Grammar:** both new tags, all old spellings, case/punctuation, title-route order, directive-only HTML descriptions, prose rejection, code/Markdown links, nested tags, duplicate directives, and cross-field polarity conflicts.
- **Inheritance:** true/false/absent, multiple area and project levels, false then true, reporting-root boundaries, task moves, explicit tag precedence, invalid types, duplicate keys, missing/ambiguous parents, cycles, and depth handling.
- **Ownership:** Google reroutes an untouched root; a vault-edited root is retained; Google and vault clock overrides differ; inherited state is never emitted as an explicit tag; alias migration does not turn edited text into an untouched baseline.
- **Session integration:** non-MEET and MEET starts, restart, swaps, link additions/drops, close after deferral, mixed and unresolved lineups, inherited event clusters, sync past-event creation, and reconcile settlement.
- **History:** old closed rows remain byte-identical across setting changes; stored totals stay fixed; only current-policy drift changes. Alias migration alone leaves clock totals and drift unchanged.
- **Migration:** old years and `done/`, completed/canceled rows, old title-token layout, manually edited badges, code/prose exclusions, conflict reporting, interruption between note and journal writes, retry, rollback, and a second no-op pass.
- **Clients:** Rust and both JavaScript implementations consume the same vectors; inherited visuals agree in editor and Reading view; unsaved edits work; changing an ancestor refreshes agenda/preview; old JSON fallback remains supported.
- **Warnings:** dry-run, unchanged sync, repeated aliases, JSON purity, quiet mode, and no automatic remote Calendar write.

A decisive scratch-vault acceptance scenario is: love=true → child with no setting → ordinary task and Calendar event `Lunch @love` both resolve off-clock without added tags; a false child and a `#on` event resolve Worked; all-off starts/closes write `[off::]`; a mixed session writes `[t::]`; an eligible ended inherited event settles once; changing love back to false affects new decisions but leaves closed clocks untouched. Follow that with migration and sync on an edited historical event to prove user ownership survives normalization.

**Recommended solution.** Adopt `#off` and `#on`, keep all three legacy off spellings as warned-compatible Google input, and implement nearest-ancestor `offclock` defaults through a contextual task-clock resolver shared in contract across bob-cli and Obsidian. Keep explicit tags separate from inherited results, use the final Event Task root as its policy anchor, retain ordinary task residence semantics, and preserve the existing counted-links and frozen-history rules. Deploy the readers and writers together, perform a journal-aware historical task-tag migration, then enable `offclock: true` on `love.md` after previewing its settlement impact. This meets the user’s intent while keeping both future overrides and past time records trustworthy.
