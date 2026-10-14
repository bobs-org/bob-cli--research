# Capture `*` as reverse task dependency (blocks)

> **Research query:** Add a `*` capture syntax, parallel to `&`, so a new
> task can block a specified existing task (the inverse edge). When that
> blocked task has a Task Link under today's daily file, remove the link
> and delete the Pomodoro entry if it becomes empty. Critique the idea,
> adjust requirements where justified, and recommend how to implement it
> in `bob capture` and Bob Mac Capture.
>
> Independent swarm report (`__grk`). Does not consult peer swarm reports.

## Bottom line

**Build it. Treat `*` as inverted `&`, and keep Depends-On as the only
authored edge.**

`&note:block-id` already means "this capture's task depends on that task."
`*note:block-id` should mean "this capture's task is a prerequisite of that
task": the specified task gains a Depends-On link to the captured task, flips
to Blocked `[?]` when the captured task is open, and loses its live Task
Links under today's open Pomodoros through the existing
`consume_live_links` path (PDL2 already deletes an emptied entry, including
a running timed one).

The request is a good idea. The daily moment it serves — "I cannot do Y
until I do this new X" — is exactly when capture is open, and today it
takes a second gesture on Y (Task Card Depends on). The vault already
forbids Blocked work from remaining planned today; capture `&` and
reconcile already enforce that. `*` is the missing authoring direction.

The source of truth stays the dependent's `⛓️ **DEPENDS ON:**` line
(`decisions:task-deps-are-depends-on-links`). The generated
`🧱 **BLOCKS:**` child on the new task is a mirror, never an authored
edge (`docs/task-dependencies.md` §14, BR26).

I make sixteen requirement adjustments, **ADJ-1…ADJ-16**, in
[Requirement adjustments](#requirement-adjustments). The full design is in
[Recommended solution](#recommended-solution).

---

## Is this a good idea

**Yes.** The evidence:

1. **The inverse of `&` is a real capture-time thought.** `&` answers "this
   new work waits on something that already exists." The dual is "this new
   work is why something I already planned cannot start." That is a capture
   thought, not a Task Card thought. The Task Card `b` row edits the
   *dependent*. To express "X blocks Y" today you must open Y and add X as
   a prerequisite — after X exists, and after you have looked Y up. Capture
   `*` names Y while creating X.

2. **Blocked tasks already keep no live Task Links.**
   `decisions:projects-block-from-prj-line` and `docs/task-dependencies.md`
   §5 / §13.5 / PDL1–PDL2 make this a vault law. Capture `&` already calls
   `consume_live_links` in `src/native/capture/project_deps.rs` whenever the
   dependent ends `[?]` with an open prerequisite (`dependencies.rs` around
   the "Any `&` that leaves its dependent Blocked" comment;
   `tests/cli/capture/parse_dependency.rs::capture_dependency_consumes_links_when_newly_blocked`).
   The request's "remove the task link, and the pomodoro iff empty" clause
   is that function, applied to the `*` *target* instead of the `&` owner.
   Do not invent a second cleaner.

3. **The writer machinery already coordinates multi-note batches.**
   `capture/dependencies.rs` resolves locators, rejects cycles, merges
   Depends-On lines, derives `[dependsOn::]` / `[id::]`, flips `[?]`,
   stamps existing dependents, mirrors BLOCKS, promotes prerequisites,
   consumes today-links, and rolls back on preimage failure. `*` is the
   same planner with owner and target swapped.

4. **Mac Capture is a thin client of bob**
   (`decisions:mac-capture-is-a-thin-client`). `&` already has parse spans
   (`dependency_sigil` / `dependency_note` / `dependency_block_id`), a
   `task_dependency` completion context, a picker card, and preview from
   `dependency_update`. `*` lands in bob-cli first; the app decodes a new
   context and caption.

5. **Phase 2 of BLOCKS (bob-cli-3p) is the Obsidian counterpart, not a
   blocker.** `docs/task-dependencies.md` §14.12 defers "editing from the
   prerequisite (chip × / ＋ on BLOCKS rows, a Task Card Blocks row)" to a
   later epic. Capture `*` is that authoring direction for the capture
   grammar. It does not need the plugin stage, and the plugin does not
   need to wait on it.

The idea would be a bad idea if `*` authored a second graph, if it
silently replaced today's work with the new task, or if the sigil ate
Markdown italics and `=x*` park. The adjustments below close those.

---

## Requirement adjustments

Each adjustment is a justified change to the request. The lead should
keep or drop them explicitly.

### ADJ-1 — Write Depends-On on the specified task; never author BLOCKS

The request says the new task "should have a task dep link" in the
opposite direction from `&`. The only legal dep link is a Depends-On
entry *on the dependent* (`decisions:task-deps-are-depends-on-links`).
So `Fix CI *sase:flaky` writes:

```markdown
# sase.md (the specified task — dependent)
- [?] #task Fix the flaky test ^flaky
  - ⛓️ **DEPENDS ON:** [[inbox_note#^fix-ci]]

# mac_inbox.md (the captured task — prerequisite)
- [ ] #task Fix CI ^fix-ci
  - 🧱 **BLOCKS:** [[sase#^flaky]]
```

The BLOCKS line is the existing mirror (`capture/blocks_mirror.rs`),
staged in the same batch. Reconcile remains authority (BR26).

### ADJ-2 — Keep the `*` sigil, with a Markdown-italic carve-out

Empirical `bob capture-parse` on this checkout (2026-10-14):

| Draft | Current mode | Body |
| --- | --- | --- |
| `Fix CI *sase:flaky` | `task` | `Fix CI *sase:flaky` (literal) |
| `Buy milk *urgent*` | `task` | `Buy milk *urgent*` (literal italics) |
| `*` | `task` | `*` |
| `=*` | `pomodoro_close` | park-all close |
| `=x*1` | `pomodoro_close` | park task 1 |
| `3 * 4` | `task` | literal |
| `Buy milk &foo:bar` | `task` + `dependencies` | `&` already stripped |

`*` is free as a *directive* today. It is busy as Markdown emphasis and as
the park operator *inside* `=x…` / `=*…` tokens.

Reuse `&`'s token-start / leading-trailing-run / `\&`-style escape rules
(`src/native/capture_language/dependencies.rs`, already generalized over
sigil `&` and `!` via `scan_modifier_with_sigil`). Add one extra carve-out
that `&` does not need:

**A whitespace-delimited token that starts and ends with `*` and contains
no `:` is literal Markdown emphasis, never a picker or modifier.**
`Buy milk *urgent*` stays a task titled `Buy milk *urgent*`.
`Fix CI *sase:flaky` is a complete blocks modifier.
Bare `*` at the start of an item or as the last token still opens the
picker (today it would create a task named `*`; that capture is unused).

Escape: `\*sase:flaky` leaves visible `*sase:flaky` in task text, matching
`\&`.

### ADJ-3 — Session-operator `*` stays park

Close tokens are a different class: they start with `=`
(`close_selection.rs` treats `*` after `=x` / as `=*` as park). A `*`
blocks modifier never lives inside an `=` token. `=x *sase:flaky` is a
close plus a blocks modifier; session operators already reject `&`
(`operator_dependency_error`). Reject `*` on close/start/adjust/shift the
same way. Freeze tests: `=*`, `=x*1`, `=x1*2!3`, `==*`.

### ADJ-4 — Always mint a block ID on the captured blocker

`&` may create an ID-less dependent; BLOCKS mirror mints later only when
an open prerequisite needs to list it (`plan_new_task_dependencies`,
"the dependent needs a `^block-id` before any prerequisite can list it").

`*` inverts that. The *specified* task's Depends-On line must link to the
captured task, so the captured task must have a trailing `^id` before the
edge is written. Mint with `capture_block_ids::mint_block_id` in the same
staged batch when the owner has none, even if `dependencies.blocks_lines`
is off. Honor an explicit `@route^id`. Report the mint as
`minted_dependent_block_id` is reported today, or a parallel
`minted_blocks_owner_block_id` if the existing field's name is too
dependent-centric — prefer reusing the field and documenting that for `*`
it is the blocker.

### ADJ-5 — "Pomodoro section" means the Pomodoro *entry*

The request says "the pomodoro iff that pomodoro section becomes empty."
The vault unit is a column-0 Pomodoro *entry* under `## Pomodoros`
(`glossary:pomodoro`), not the heading. PDL2: when the consumed link was
the entry's last child, delete the entry; a running timed entry may go.
`consume_live_links` already runs `plan_empty_pomodoro_removals`. Reuse it.
Leave `## Pomodoros` in place. Closed entries and struck links stay
byte-identical (PDL4, PDL5). A prose bullet loses only the link token
(PDL6). A link-only bullet takes its subtree (PDL7).

### ADJ-6 — Consume the specified task's live links whenever it is `[?]` after the write

Match capture `&` and the Depends-On consumption plan
(`plan:202610/depends_on_consumes_today_links.md`): consume when the
dependent ends `[?]` with an open prerequisite, including a dependent that
was already `[?]`. Scope is **today's** daily file only
(`pomodoro::day_file_for`), open entries only.

When the `*` target is a recognised project's `^prj`, apply §13.10: tag
residents `#prj_is_blocked`, consume *their* live links too, refuse a
same-note / descendant target (a project cannot wait on its own tasks).
That is a bigger hammer than blocking one ordinary task; the dry-run
preview must say so (ADJ-14).

### ADJ-7 — Do not auto-link the new task into the hole Y left

Removing Y from today and silently inserting X in the same Pomodoro would
invent a replacement-link gesture. `decisions:unblocked-tasks-are-offered`
keeps auto-linking off even at close time. Composition already covers the
"X takes Y's slot" intent:

```text
Fix CI @sase:fix *sase:flaky
```

That creates X, links X under the current/next Pomodoro (existing `:`
meaning), and unlinks flaky. Without `:`, X lands as an ordinary inbox
task (Ready, unstamped, NEW). That preserves freshness: creation never
stamps (`glossary:task-freshness`).

**Existing-task owner** (`*sase:flaky @body+exercise`): exercise is an
already-identified task. Apply commitment transfer the way `&` promotes
prerequisites: raise the owner to at least the blocked task's pre-capture
lane (and for `^prj`, the strongest among `^prj` and residents; never
raise a `^prj` *target*). New-task owners skip this promotion so they stay
in NEW unless the user also linked them.

### ADJ-8 — New parse/complete context `task_blocks`; do not overload `task_dependency`

Mac hardcodes the `&` picker: `CapturePickerPresentation.scopeSymbolText`
returns `"&"` and `scopeCaption` returns `"Depends On"` for `.dependency`;
`CapturePanelModel` routes `completion.context == "task_dependency"` to
`handleDependencyCompletion`. Overloading that context would insert `&`
replacements for a `*` picker, or require a tangle of role flags in every
hardcoded `&`.

`!` already has its own context (`task_complete`) despite sharing the
locator lexer with `&`. Give `*` the same treatment:

| Layer | `&` | `*` |
| --- | --- | --- |
| Need (partial) | `task_dependency` | `task_blocks` |
| Need (ownerless) | `dependency_target` | `blocks_owner` |
| Mode (existing owner, no new task) | `task_dependency` | `task_blocks` |
| Mode (new task) | `task` + `dependencies` | `task` + `blocks` |
| Complete context | `task_dependency` | `task_blocks` |
| Spans | `dependency_sigil/note/block_id` | `blocks_sigil/note/block_id` |
| Picker scope / caption | `&` / Depends On | `*` / Blocks |

Schema version stays 1; fields are additive. Old Mac ignores them and
still submits a fully-typed `*note:id` once new bob accepts it. New Mac
plus old bob never opens the picker (`*` stays body text, as today).

### ADJ-9 — The `*` picker lists open tasks, today's ledger first

`&` searches the whole vault including completed history, because a new
task can wait on finished work. `*` names a task that will become
Blocked; closed/cancelled targets are useless (ADJ-11). Empty-query
order:

1. Open tasks with a live Task Link under today's open Pomodoros (the
   consumption use case)
2. In Progress, then Next
3. Other open tasks grouped by note
4. Hidden last within a section

Queries use the same tiered AND-term matcher as `&` / `:`. Candidates
reuse the `&` wire shape (`note_path`, `locator`, `group`,
`already_dependency`, `disabled_reason`, `requires_block_id`, Bob-authored
`replacement` that already includes the `*` sigil). `already_dependency`
means "the owner is already a prerequisite of this candidate."
`disabled_reason` covers self, duplicate ID, cycle, project-internal
`^prj`, and closed (if history is shown at all, keep them disabled).

### ADJ-10 — Support an existing-task owner, matching `&`

The request talks about "the new task." `&` also updates an explicit
existing parent (`&foo:bar @body+excercise`). The ownership resolver
(`resolve_execution_ownership` in `capture_language/dependencies.rs`) is
shared. Supporting `*sase:flaky @body+exercise` ("exercise blocks flaky")
is the cheap dual and avoids a special case that would later surprise.
Ownerless `*sase:flaky` stays incomplete (`blocks_owner`), never a
star-named task.

Narrow `@route:id` alias as a *blocks* owner applies only when at least
one `*` modifier exists, there is no body, and the colon token is
unsuffixed — the same gate `&` uses. Without `*`, `@route:id` keeps its
link meaning.

### ADJ-11 — Refuse closed, cancelled, and missing `*` targets

A Done/Cancelled task does not wait. Missing notes, missing block IDs,
ambiguous basenames, self, and new cycles fail closed with the same
actionable style as `&` (`reject_new_cycles`). Repeats are idempotent
(`0 added`). ID-less *targets* use the existing Add-block-ID flow
(`capture-task-id --note-path`) before they can be blocked.

### ADJ-12 — bob-cli then Mac; plugins out of scope

The request names `bob capture` and Bob Mac Capture. Ctrl+Shift+P already
writes the edge from Y's side. Reconcile remains the backstop if a
capture write skips a today-link. Do not bundle bob-cli-3p, vault
migration, or a plugin "Blocks" stage into this epic.

### ADJ-13 — `&` and `*` compose; one item may carry both

`Fix CI &ops:access *sase:flaky` means: the new task depends on
`ops#^access` and is a prerequisite of `sase#^flaky`. Independent
arrays, one cycle check on the merged graph (including other items of
the same draft). `Fix CI *sase:flaky &sase:flaky` is a direct cycle and
refuses. Session operators, section bullets, project-note construction,
and Pomodoro-note `#` still reject both families.

### ADJ-14 — Dry-run preview names the reverse write and the unlink

Mac already shows `New task · depends on …` from `dependency_update`.
`*` must not be labelled "Create task" when it is owner-only, and must
not look like `&`. Preview lines, all from bob:

- `New task · blocks "Fix the flaky test"` / `Would block "…" · unlinked from today`
- The specified task's block (`roles` include `"dependency"`) with the
  new Depends-On child and `[?]`
- The captured task's block (`"dependency_target"`) with BLOCKS + minted
  `^id`
- `removed_pomodoro_links` and emptied `pomodoro_blocks` (`removed`)
- For `^prj` targets: resident count and `#prj_is_blocked`

Human CLI: `would block "Fix the flaky test" · removed 1 live Pomodoro
link` (and `· deleted emptied Pomodoro` when PDL2 fires).

### ADJ-15 — Quote `*` on the CLI; Mac types it raw

Unquoted `*` is a zsh glob, as unquoted `&` is bash job control. Docs
and `--help` show quoted examples. The Mac panel is not a shell; typing
`*` is the trigger. Same class of issue `&` already accepted.

### ADJ-16 — Later `@route:id` on Y may drop the new edge

`decisions:capture-link-drops-blocking-deps` (2026-10-13): linking a
task that is Blocked only by its own open prerequisites drops those
links and then links. So after `Fix CI *sase:flaky`, a later
`@sase:flaky` can drop the Fix-CI edge. That is the existing "I want to
work on Y anyway" gesture, already previewed as `dropped_dependencies`.
Do not make `*` edges sticky. Mention the composition in `docs/capture.md`
so it is not a surprise.

---

## Current system (evidence)

### Grammar and lexer

- `&` and `!` share `scan_modifier_with_sigil` in
  `src/native/capture_language/dependencies.rs`. A third sigil is a
  parameter, not a new scanner. Locator rules (vault-relative note,
  quoted components, `\"` / `\\`, block-ID `A-Z a-z 0-9 -`) stay.
- Directives occupy the parent leading run and the trailing run past
  `@` / `#` / `s:` / `p:` / clipboard markers. Mid-line `*foo:bar`
  stays body text, matching `&`.
- `extract_line_dependencies` currently keys off `b'&'`. Generalize to
  a per-sigil scan or scan `*` in parallel into `ItemBlocksSet`.
- Fail-closed: a draft that contains `*` modifiers never captures as a
  plain task that swallowed the token. Until the writer lands, parse
  may exist with execution refused (the `&` epic's phase-1 pattern in
  `plan:202610/capture_task_dependencies.md`). Prefer landing parse and
  writes in sequence so Mac never highlights a modifier submit then
  rejects.

### Writer

`src/native/capture/dependencies.rs` is the template. For each `*`
target, call the *existing-dependent* write path with:

- `dependent` = resolved `*` target
- `prerequisites` = `[captured owner]` (after mint)
- then `consume_live_links(planner, bob_dir, target_route, &blocked_ids)`
- then BLOCKS mirror **on the owner** (`BlocksDelta::Add` of the target)
- cycle check via `reject_new_cycles` with extra edges from this item

New-task path today (`plan_new_task_dependencies`) augments the captured
line with a Depends-On *child*. For `*` the captured line gets a BLOCKS
child instead (mirror), and Depends-On is written on each target note.
If the same item also has `&`, the captured line gets both children in
canonical order: Depends-On first, BLOCKS after
(`docs/task-dependencies.md` slot table).

### Consumption

`consume_live_links` in `src/native/capture/project_deps.rs`:

1. Resolve today's day file.
2. For each block id, `capture_task_toggle::plan_link_removal`.
3. `plan_empty_pomodoro_removals` + `apply_empty_pomodoro_plan`.
4. `planner.stage` the day file.

Returns `removed_links` and `pomodoro_refs` for emptied entries. Capture
JSON already has `removed_pomodoro_links` and batch `pomodoro_blocks`.
Reuse both.

### Mac

Thin-client map for `&` (do the dual, do not parse `*` in Swift):

- `capture-parse` spans and `needs: ["task_blocks"]` open the picker
- `capture-complete` context `task_blocks`, Bob-authored `replacement`
  (`*note:id`, quoted when needed), `trigger_removal_range` for
  Backspace-on-empty-filter
- `handleBlocksCompletion` cloned from `handleDependencyCompletion`
  with scope `*` and caption `Blocks`
- Command-Return captures only when the owner is complete; otherwise
  keep the draft open ("Add task text or @note+id, then capture")
- Shift-Return does not append `=` (same as `&`)
- Preview from bob's `dependency_update` plus additive `blocks_update`
  / `removed_pomodoro_links`; Swift never infers consumption
- Older Bob: `*` remains body; no picker. Older app: typed `*note:id`
  still submits to new bob.

`just portable-check` on Linux; macOS typecheck/tests on a Swift host /
CI (`bob-mac-capture/AGENTS.md`).

### Decisions that constrain the design

| Decision | Constraint on `*` |
| --- | --- |
| `task-deps-are-depends-on-links` | Author the target's Depends-On line |
| `projects-block-from-prj-line` | `^prj` target blocks residents; consume their links |
| `subprojects-inherit-project-blocking` | Ancestor `^prj` cascades; refuse descendant targets |
| `today-is-read-from-the-ledger` | Today = live links under today's open Pomodoros |
| `task-lanes-are-sticky` | Unlink does not Ready a Next/Pending task; `[?]` overlays |
| `task-status-is-derived` | Writers change inputs; hooks remain authority |
| `mac-capture-is-a-thin-client` | Grammar, preview, writes in bob |
| `capture-link-drops-blocking-deps` | Later link of Y may drop the new edge (ADJ-16) |
| `unblocked-tasks-are-offered` | Do not auto-link X into Y's hole (ADJ-7) |
| `cli_rules.md` | No subcommand under `bob capture`; additive protocol fields |

---

## Alternatives considered

### A. No new syntax; use Task Card on Y after capturing X

Works today. Misses the capture-time thought and forces a second lookup.
Rejected as the primary design; it remains the Obsidian path.

### B. Post-submit "block a today task?" picker

Capture does not prompt (`decisions:unblocked-tasks-are-offered` keeps
choice in-panel and explicit). A second step after every new task would
be noise. A sigil is the right opt-in.

### C. Author BLOCKS on X and let reconcile invert it

Rejected by `decisions:task-deps-are-depends-on-links` and §14: BLOCKS
is never an edge. Hand-edited BLOCKS is restored. Capture would fight
reconcile.

### D. Different sigil (`>`, `~`, `blocks:`)

`>` and `<` are shell redirects. `~` is close-drop. `blocks:sase:flaky`
is unambiguous and picker-hostile. `*` is what was asked, is one key in
the Mac panel, and is distinguishable from `=x*` with ADJ-2 and ADJ-3.
Keep `*`.

### E. Overload `task_dependency` with `role: "blocks"`

Fewer Mac types, more bugs in hardcoded `&` captions, Backspace, and
replacement. `!` already split off. Split `task_blocks` (ADJ-8).

### F. Auto-replace Y's Pomodoro link with X

Looks helpful and steals the day. Composition with `:` is enough
(ADJ-7).

---

## Recommended solution

### User-facing contract

`*note:block-id` means "the task I am capturing or explicitly targeting
is a prerequisite of `note.md` / `^block-id`." Locator spelling matches
`&` / `!`: `&projects/foo:bar` dual is `*projects/foo:bar`; spaces use
`*"Shopping List":bar`.

| Draft item | Reading |
| --- | --- |
| `Fix CI *sase:flaky` | New inbox task; mint `^id`; `sase#^flaky` Depends-On that id; flaky `[?]`; flaky's today-links consumed; emptied entry deleted; X gets BLOCKS mirror |
| `Fix CI @sase:fix *sase:flaky` | Same, and X is Pomodoro-linked Next (existing `:` meaning) |
| `Fix CI @home *sase:flaky *cash:budget` | X blocks two tasks, typed order, one batch |
| `Fix CI &ops:access *sase:flaky` | X depends on access and blocks flaky |
| `*sase:flaky @body+exercise` | No new task; exercise becomes a prerequisite of flaky (`task_blocks`) |
| `*sase:flaky @body:exercise` | Same via the narrow unsuffixed colon alias |
| `*sase:flaky` | Incomplete: `blocks_owner` |
| `*`, `Fix CI *sa`, `Fix CI *sase:` | Incomplete: `task_blocks` (picker open) |
| `Buy milk *urgent*` | Literal italics (ADJ-2) |
| `3 * 4`, `R*D` | Literal |
| `Fix CI \*sase:flaky` | Literal `*sase:flaky` in the title |
| `=*`, `=x*1` | Park close (ADJ-3) |
| `=x *sase:flaky` | Refused: blocks modifier on a session operator |

### Write effects (one atomic batch)

For each complete `*` target, with owner O (new or existing) and target T:

1. Resolve T; refuse closed/missing/self/cycle/project-internal.
2. Ensure O has a trailing `^id` (mint if needed).
3. Merge `[[O]]` into T's managed Depends-On line and `[dependsOn::]`.
4. If O is open: T → `[?]`; stamp T if T already existed (same helper
   `&` uses for existing dependents); do not stamp a newly created O.
5. If T is `^prj` with an open O: resident `[?]` + `#prj_is_blocked`.
6. `consume_live_links` on T (and residents when `^prj`).
7. BLOCKS mirror on O listing T.
8. Existing-task O: commitment transfer from T's pre-capture lane.
9. New-task O: leave Ready/NEW unless the item also linked O.
10. Idempotent repeats; dry-run plans the same final blocks; failure
    rolls the batch back.

### JSON (schema v1, additive)

Per item, parallel to `dependencies` / `dependency_target`:

```json
{
  "mode": "task",
  "blocks": [
    {
      "raw": "*sase:flaky",
      "note": "sase",
      "block_id": "flaky",
      "quoted": false,
      "range": {"start": 7, "end": 19}
    }
  ],
  "blocks_owner": {"kind": "new_task", "route": "mac_inbox"}
}
```

Capture success reuses `dependency_update` for T (T *is* the dependent)
and reports O as a `dependency_target` task block with BLOCKS lines.
Add `removed_pomodoro_links` when consumption ran. Optional additive
`blocks_direction: "blocks"` on the update so Mac labels "blocks"
instead of "depends on" without guessing from sigils.

### Implementation map

Mirror epic `bob-cli-3u` (`plan:202610/capture_task_dependencies.md`),
smaller because locator, graph, Depends-On merge, BLOCKS mirror, and
`consume_live_links` already exist.

1. **Grammar (bob-cli).** Sigil `*` in the shared modifier scanner;
   italic carve-out; spans/needs/mode; rewrite strips modifiers;
   `\&`-style escape; freeze the contract table; fail-closed execution
   until writes land. Tests next to `tests/cli/capture/parse_dependency.rs`.
2. **Completion (bob-cli).** Context `task_blocks`; open-only catalog;
   today-ledger-first order; inverted `already_dependency` / cycle
   guards; replacement formatter with `*`. Shell completion lists the
   new context. Tests next to `complete_dependency.rs`.
3. **Writes (bob-cli).** Invert owner/target in a focused
   `plan_blocks_modifiers` next to `plan_new_task_dependencies` /
   existing-dependent writes; mint on O; Depends-On on T; consume T;
   BLOCKS on O; `^prj` side effects; compose with `&`; preimage
   rollback. Tests: the contract table, PDL1/PDL2, already-blocked T,
   `^prj` residents, emptied running entry, dry-run parity, cycles,
   `&`+`*` in one item, `=x*1` unchanged.
4. **Mac.** New picker source cloned from dependency; caption Blocks;
   decode additive parse/complete/preview fields; no Swift locator
   parsing; README examples. Tests: old/new JSON fixtures, Unicode
   splice, Command-Return owner gate, italic drafts do not open the
   picker, `=x*1` still close.
5. **Docs / verification.** `docs/capture.md` table + section "Blocking
   tasks with '*'"; `docs/task-dependencies.md` writer table (capture
   `*` next to capture `&`); `docs/getting-started.md` one-liner.
   `just check` on bob-cli; macOS `just all` / CI for the app.

`cli_rules.md`: this is grammar on `bob capture`, not a new subcommand.
Help stays excellent; examples quoted.

### Suggested freeze tests (non-exhaustive)

- `Fix CI *sase:flaky` creates X with `^id`, T Depends-On X, T `[?]`, T
  unlinked, emptied planned Pomodoro gone.
- Same with a second child under the Pomodoro: entry kept.
- T already `[?]` with a stale live link: link still consumed.
- `^prj` target: residents tagged, their links consumed, same-note
  resident target refused.
- `Fix CI @sase:fix *sase:flaky`: X linked, T unlinked.
- `*sase:flaky @body+exercise`: no new task, exercise listed on flaky.
- `Buy milk *urgent*`: body unchanged, no `blocks`.
- `=*`, `=x*1`: `pomodoro_close`.
- Direct and batch cycles refuse; vault intact.
- Dry-run JSON equals real-run JSON except `dry_run`.

### What I would not do

- A plugin gesture in the same epic.
- Auto-linking X into Y's Pomodoro.
- A second stored graph on BLOCKS.
- Overloading `task_dependency`.
- Making `*` edges survive a later capture link drop.
- Changing lane stickiness or freshness stamping rules.

---

## Verdict

Ship `*` as inverted `&` in bob-cli, then Bob Mac Capture. The
consumption rule is already implemented; the missing piece is an
authoring sigil that writes Depends-On on the *other* task and mints an
id on the new blocker. Keep `*` as requested, with the italic carve-out
and the `=` park tokens left alone. Preview the reverse write and the
unlink before submit. That is the smallest design that matches the
vault's dependency law and the way capture already works.
