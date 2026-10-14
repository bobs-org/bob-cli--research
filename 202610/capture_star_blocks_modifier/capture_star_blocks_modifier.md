# Capture `*`: "this new task blocks that one" — consolidated research

> **Research query:** How should `bob capture` and Bob Mac Capture best support a new `*`
> syntax that works like `&` but records the task dependency link in the opposite
> direction (the new task blocks the specified task), and that removes the blocked task's
> Task Link from today's daily file, plus its Pomodoro iff that Pomodoro section becomes
> empty? Is this a good idea, would a different approach be better, and which requirement
> adjustments are justified, ending with a recommended solution?

![Capture star infographic: N *T writes N into T's Depends-On line and removes T's live Task Links under today's open Pomodoros; the shared cleanup is fixed first because 13% of Task Links carry child notes; bob-cli owns the engine while Bob Mac Capture adds a direction-aware picker; ship star as & with the roles swapped](capture_star_blocks_modifier_infographic.png)

## Bottom line

- **[Build it.](#is-this-a-good-idea)** The usual moment to record a blocker is while you
  are looking at, or working on, the task it blocks. `*` lets one capture create the
  blocker and attach it. Today that needs a two-item draft with a block ID you invent
  yourself, and it cannot reach blocked tasks in nested notes at all.
- **Add no new data model.** `N *note:id` means "add N to `note#^id`'s Depends-On line."
  The edge lives only on the blocked task's `⛓️ **DEPENDS ON:**` line, and N's
  `🧱 **BLOCKS:**` line is the usual generated mirror. The existing writer for `&` on an
  existing dependent (`plan_existing_task_dependencies`) already does nearly all of this
  when you swap the roles.
- **Your third requirement is already a vault invariant.** A Blocked task keeps no live
  Task Link under today's open Pomodoros. Capture `&` and `bob task reconcile` already
  enforce this (`docs/task-dependencies.md` §5, §13.5). `*` should reuse that path, not
  get a rule of its own. The path is not ready to reuse as-is, though. Fix four things
  before `*` ships, because `*` makes this path the common case:
  1. **It deletes your notes.** A link-only bullet is removed with its whole subtree
     (PDL7). In the last 90 daily notes,
     **[13% of Pomodoro Task Links (212 of 1,613) have notes under them, on 57 of 90 days](#vault-measurement).**
     `*`'s main use is "I was working on T and hit a blocker", which is exactly when T's
     link has fresh notes under it.
  2. **It is silent.** Removed links and deleted Pomodoros, including the *running*
     session, never reach `pomodoro_blocks` or any structured field. The only signal is a
     one-line warning. This is bead `bob-cli-7l`.
  3. **It deletes more than it emptied.** It removes *every* childless entry in the day
     file, not only the one this capture emptied.
  4. **It matches link text exactly.** It looks for the literal string
     `[[route#^id]]`. Nested-note targets, which `*` makes reachable for the first time,
     would be missed.
- **Keep the `*` sigil, with [Markdown guards](#grammar-contract)** that `&` never needed
  (`*italic*`, `**bold**`, `* bullet`, `5 * 3`).
- **[Requirement adjustments](#explicit-requirement-adjustments)** and
  **[the recommended solution](#recommended-solution)** follow below.

## What the star sigil means

Let N be the new task, T an existing task it blocks with `*`, and P an existing
prerequisite. Arrows mean "depends on":

| Draft | Stored edge | Line that changes |
| --- | --- | --- |
| `N &P` (today) | N → P | N's Depends-On |
| `N *T` | T → N | T's Depends-On |
| `N &P *T` | T → N → P | both ("insert between") |
| `*T @route+id` (existing owner) | T → `route#^id` | T's Depends-On |

```text
bob capture 'Ask Kelly for references *job:cleanup'
```

```markdown
# job.md (T, the dependent)
- [?] #task Do cleanup tasks! ^cleanup
  - ⛓️ **DEPENDS ON:** [[mac_inbox#^ask-kelly-for-references]]

# mac_inbox.md (N, new, block ID minted automatically)
- [*] #task Ask Kelly for references! ^ask-kelly-for-references
  - 🧱 **BLOCKS:** [[job#^cleanup]]
```

T's live links under today's open Pomodoros are consumed. N inherits T's commitment
([A6](#explicit-requirement-adjustments)). The example assumes T was Next or Pending; a
Ready T leaves N Ready. When N closes, T recovers with an `[unblocked::]` tickler and is
offered as a successor; nothing re-links it automatically. cld confirmed this round trip
already works using the two-item spelling.

## Is this a good idea

**Yes.** All [four researchers](#about-this-report) agree, and so do I:

1. **It captures the dependency when it is discovered.** `&` only works when the
   prerequisite already exists. `*` covers the opposite, more common thought: "I can't
   do T until I do this new thing."
2. **It adds no new model.** Every engine already understands the result: reconcile,
   chips, the Ready/Blocked lanes, the BLOCKS mirror, successor offers, and the Mac idle
   agenda.
3. **It does more than the workaround.**
   `N @inbox^id` followed by `&inbox:id @T-route+T-id` works today, but `@route` cannot
   contain `/` (`is_route_token`, `markers.rs:220`). Tasks in nested notes are
   unreachable that way.
4. **It respects the thin-client rule.** All semantics land in bob. The Mac app only
   presents them.

### Costs to accept knowingly

- **An ordinary capture now edits notes you didn't touch.** It can change T's note, a
  `^prj`'s residents, and today's ledger, including deleting a running timed session. The
  preview is the only safety net, and today it does not show this even for `&`.
- **Grammar budget.** `*` already means Next (`[*]`) and park (`=x*`, `=*`), and it is
  Markdown emphasis and a list marker. cld's mnemonic helps: `*T` hands T's star (its
  commitment) to the new task.
- **The block is soft.** Under `decisions:capture-link-drops-blocking-deps`, a later
  `@job:cleanup` link drops N from T's line. That is intended ("work on T anyway"), and
  the preview already reports `dropped_dependencies`.
- **Lanes don't survive Blocked.** T loses Next or Pending for good and recovers to
  Ready. This is the established design; `*` just makes it happen more often.
- **Two release trains.** The Mac half is gated by macOS CI, and `bob` and the app are
  installed separately.

### Alternatives considered

All four reports converge on rejecting these alternatives:

| Alternative | Verdict |
| --- | --- |
| Keep the two-item draft | Zero work. Too slow at the moment it matters, and it cannot reach nested notes. |
| Task Card on T after capturing N | A second lookup. It remains the Obsidian path; the reverse Blocks stage (`bob-cli-3p`) is complementary, not a substitute. |
| Directional `&` (`&>`, `&^`) | Awkward to type and parse; less visually distinct. |
| `blocks:` keyword | Easy to discover but slow, and hostile to the picker. |
| Direction toggle only in the Mac picker | The grammar must be textual in bob. Fine later as a convenience that rewrites `&`↔`*` through `capture-rewrite`. |
| Author BLOCKS on N and let reconcile invert it | Violates `task-deps-are-depends-on-links`: BLOCKS is never read back. |
| Auto-put N into T's vacated slot | Invents an auto-link, against `unblocked-tasks-are-offered`. Many blockers are waits ("Wait for Joe's review"). Use explicit linking instead ([A5](#explicit-requirement-adjustments)). |
| Other sigils (`?`, `%`, `>`, `\|`, `~`) | `?` is the only serious runner-up: T becomes `[?]`, and the lexer doesn't use it. `>` is a shell redirect and a blockquote, `~` is the close-drop syntax, and `\|` breaks wikilinks and tables. Keep `*`, which sits next to `&` on the keyboard (⇧7/⇧8) and pairs with it visually. |

## Verified facts and where the reports disagreed

### Facts I checked in source

| Claim | Evidence (bob-cli `23bee1f` unless noted) |
| --- | --- |
| `&` and `!` already share a sigil-generic scanner | `capture_language/dependencies.rs`: `scan_modifier_with_sigil`. The `&`-specific spots are the line scan, the bare check, `\&` unescaping, and the diagnostics. |
| The note-name check accepts `*` | `validate_note` (`dependencies.rs:197`) rejects only empty, absolute, `.` and `..` components. Obsidian file names cannot contain `*`, so rejecting it is free. |
| `@route` cannot name a nested note | `is_route_token` (`markers.rs:220`): `A-Z a-z 0-9 _ -` only. |
| Consumption matches link text exactly | `consume_live_links` (`capture/project_deps.rs:263-317`) builds `[[{route}#^{id}]]` and removes that literal string. |
| Link removal touches only open entries, but takes the subtree | `plan_link_removal` (`capture_task_toggle/links.rs:155-187`): current and future open entries only; "a link that is the sole content of its bullet is removed along with the whole bullet and its sub-bullets." The explicit Task Link toggle uses the same function. |
| The empty-entry pass removes **every** childless entry, open or closed | `plan_empty_pomodoro_removals` (`task_status_hooks/pomodoro.rs:287-311`) skips only entries with a child. |
| …and reconcile does exactly the same on every run | `task_status_hooks/sync.rs:426`; `docs/task-status-hooks.md` "Empty Pomodoros": "removes childless Pomodoro entries … open or completed." |
| Subtree deletion is an accepted contract | `docs/task-dependencies.md` §13.14 PDL7: "planned link-only bullet with authored child notes → whole subtree removed." |
| Adding a dependency transfers commitment | `docs/task-dependencies.md` §5: "If the dependent was `[*]` or `[/]`, an open target rises to at least that lane." |
| `task_blocks` is already a capture JSON field | `capture/output.rs:262` (the batch task-note preview). |
| Mac treats a line-initial lone `*` as a bullet placeholder | bob-mac-capture `CapturePanelController.swift:1054-1077`: `-`, `*`, `+` at end of line or followed by a space or tab. |
| The Mac picker hard-codes `&` | `DependencyPickerPresentation.swift:58` (`leadingSigil: "&"`) and `:300` (`insertionPrefix: "&"`). |
| Old bob treats `*` as plain text | `capture-parse` returns mode `task` with the token kept in the body (cdx and grk). |

### Vault measurement

I ran this measurement myself. I scanned the last 90 daily notes (`~/bob/2026/`). There
were 759 Pomodoro entries and 1,613 link-only Task Link bullets. Of those bullets, 212
(13%) had child bullets, on 57 of 90 days. Typical children: "Applied to Ramp, Clay, and
LangChain!", "research on athena", "Running `sase-h7` epic bead now!". These were written
while the session was open, which is exactly when `*` would consume the link.

### Disagreements and resolutions

| Topic | Positions | Resolution |
| --- | --- | --- |
| Reuse the consumption helpers as-is? | cld, grk, gem: reuse (cld: "deletion can stay; fix reporting"). cdx: unsafe as-is; reproduced it deleting notes, an unrelated empty placeholder, and an empty closed entry. | **Reuse the one path, but fix it first** ([A1–A4](#explicit-requirement-adjustments)). cdx is right that it is broader than "iff empty". cld/grk are right that it is the contract, and a second, `*`-only cleaner would drift. |
| Notes under a consumed link (PDL7) | cdx: preserve them, or refuse rather than delete. cld/grk: keep PDL7. gem: assumes notes survive, but its TX12 holds only for *sibling* notes, not children. | **Preserve them.** The [vault data above](#vault-measurement) makes this the common case for `*`. It changes an accepted contract, so it needs Bryan's approval ([Q2](#open-questions-for-bryan)). |
| Unrelated childless entries | cdx: delete only entries this capture emptied. Others are silent. | **Filter to entries this capture emptied.** This is *not* a safety fix, since reconcile deletes every childless entry anyway. It keeps the capture preview truthful to "iff it becomes empty" instead of listing unrelated deletions. |
| N's lane after T is blocked | cdx: strict `&` parity (N may become `[/]`). cld: cap at Next. grk: no transfer for new tasks (N stays NEW). | **Transfer, capped at Next** ([A6](#explicit-requirement-adjustments)). Without the transfer, blocking a Next task leaves *neither* task committed, which is the dropped-work trap sticky lanes exist to prevent. A never-worked task shouldn't be born `[/]`. |
| Existing-task owners (`*T @route+id`) | cld, grk: allow. cdx: reject in v1. | **Allow.** It is the exact dual of `&foo:bar @body+exercise`, the ownership resolver is shared, and it reaches nested dependents for existing pairs. |
| When a bare `*` opens the picker | grk: at item start or end. cld: only as the last token. cdx: at item end; bullets win. | **Only as a trailing token after other text on the same line.** A line-initial `*` is always a bullet or literal, because the Mac panel already uses it as a bullet placeholder. |
| Wire names | grk, gem: `task_blocks`. cdx: `blocking_*`. cld: `blocked_task*`. | **`blocked_task*`.** `task_blocks` already names the batch preview field, and "blocks" also means note blocks and the 🧱 line. |
| Success output for several dependents | grk: singular `dependency_update` plus a direction flag. cdx: new `blocking_update`. cld: `dependency_updates[]`. gem: `blocked_tasks[]`. | **`dependency_updates[]`**, with the singular field kept. The existing shape already describes T correctly (dependent = T, prerequisites = [N]), so old Mac builds render a true preview. |
| Version skew | cdx: advertise a capability. cld: no gate needed. | **No gate.** Ship bob first. An old bob never opens the picker, and a typed `*…` shows up visibly in the body preview, which is not destructive. Old apps degrade safely because no `dependency_*` name is reused. |
| gem's "take its slot" example `Urgent fix = *releases:deploy` | — | **Corrected.** `=` is a session operator, and `*` is rejected there. The working spelling is `Urgent fix @inbox:urgent-fix *releases:deploy` ([A5](#explicit-requirement-adjustments)). |

## Explicit requirement adjustments

| # | Your requirement | Adjustment | Why |
| --- | --- | --- | --- |
| **A1** | "remove that task link" | **Scope:** live (unstruck) links under **today's open** Pomodoros (running and planned), every occurrence. Leave alone: closed entries, `🍅` history, other days, prose outside `## Pomodoros`, and dependency lines. A missing day file means nothing to consume. Reuse the shared consumption path; don't add a `*` rule. | This is already the `docs/task-dependencies.md` §13.5 contract, and reconcile does the same within one run. |
| **A2** | (implicit) | **Match by identity, not text.** Resolve ledger links through the shared resolver: aliases, `[[#^local]]`, and basename or path spellings. | Exact `[[route#^id]]` matching misses nested targets. Reconcile would then consume them later, subtree included, with no preview. |
| **A3** | "remove that task link" | **Preserve authored notes.** When a consumed link-only bullet has children, replace the link with a plain-text bullet naming the task (no link, so it stays inert) and keep the children unchanged. A childless link bullet is deleted. Apply this in capture's consumption, which also fixes `&`. Parity for reconcile and plugins (PDG1) follows as coordinated work. | 13% of Pomodoro links carry notes. PDL7 would silently delete them. Striking the link instead is wrong because strike means "completed/retired". |
| **A4** | "the pomodoro iff that pomodoro section becomes empty" | **"Pomodoro" means the entry** (column-0 checkbox), never the `## Pomodoros` heading. **"Empty"** means no child list items at all; notes or prose keep it. Delete only entries **this capture emptied**, judged after all of the item's edits. A running timed entry may go, as you asked. **Report it loudly:** structured `consumed_links[]` and removed entries in `pomodoro_blocks` (fixes `bob-cli-7l`). Human output names the session, e.g. `− removed Task Link from JOB 10:10–10:35 (running) · deleted the empty Pomodoro`. | Turns "iff" into a testable rule and makes the destructive case visible before submit. |
| **A5** | (new) | **Order the writes "link N, then consume T."** `N @inbox:id *T`, or `#pomodoro`, puts N in the session before T's link is consumed, so the session survives. Document this as the "take its place" idiom. **Don't** auto-link by default. | This covers "do the blocker now" without a new auto-link rule. |
| **A6** | (implicit) | **Commitment transfer:** an open N rises to T's pre-capture lane, **capped at Next `[*]`** when N is created by this capture. An existing owner gets the normal `docs/task-dependencies.md` §5 transfer. A `^prj` target is never raised. | It keeps today's commitment on the actual path to T. `[/]` means work has happened, and N has had none. |
| **A7** | "the new task" | **Allow existing owners** (`*T @route+id`, bare `@route:id`, with the same narrow alias gate as `&`) and **`&` with `*` on one item.** `*T` with no owner is incomplete ("add task text or `@note+task-id`"). | It's the cheap dual of `&`. "Insert between" comes free, with the cycle check already in place. |
| **A8** | "the specified task" | **Targets must be open, editable tasks.** Nested notes are allowed. Exclude the same set as the Depends-on stage: daily notes, `done/`, `_templates`, `_generated`, `_conflicts`, dot-dirs, and fenced code. Refuse self-targets, new cycles, and malformed or multiple Depends-On lines. Refuse a `^prj` target when N routes inside that project or a descendant. Repeats are no-ops (`already_present`). | Blocking a closed task means nothing. The internal `^prj` edge is a guaranteed deadlock. |
| **A9** | (implicit) | **Always assign N a block ID** (mint one, or use the typed `^id`/`:id`), even when `dependencies.blocks_lines: false`. It stays staged until submit. | T's Depends-On line must link to N. `&` mints only for the BLOCKS mirror. |
| **A10** | (implicit) | **Markdown-safe lexing** ([grammar contract](#grammar-contract)) and **quoting on the shell** (`bob capture '… *job:cleanup'`). | Unquoted `*` is a zsh glob ("no matches found"), the same class of problem as `&`. |

`^prj` targets are allowed, with the same effects as `&` on `^prj`
(`docs/task-dependencies.md` §13.10): every open resident goes `[?]` with
`#prj_is_blocked` and loses its links. The preview must show the resident count, because
this is the biggest blast radius `*` can have.

## Grammar contract

`*` is a directive only when **all** of these hold:

1. It starts a whitespace-delimited token in the parent's leading run or the trailing
   run, exactly where `&` is allowed. Mid-line `*foo:bar` stays body text.
2. The next byte is neither whitespace nor `*`. This keeps `**bold**`, `* bullet`, and
   `5 * 3` literal.
3. The rest of the token contains no `*`. This keeps `*urgent*` literal. Reject `*` in
   the note component for both sigils, since Obsidian forbids it in file names.
4. A **bare** `*` opens the picker only as a trailing token after other text on the same
   line. A line-initial `*` is always a bullet or literal, which also protects the Mac
   bullet placeholder.
5. `\*` escapes it, as `\&` does.

`=x*…`, `=*`, and `==*` stay park operators; they live inside `=` tokens. Session
operators, section bullets, project-note construction, `!` completions, and suffixed
owners reject `*` the same way they reject `&`. Also reject `@route:id=x… *T`, because
closing and blocking in one item is incoherent.

| Draft | Reading |
| --- | --- |
| `Ask Kelly *job:cleanup` | New inbox task N; `job#^cleanup` depends on N |
| `Ask Kelly @inbox:ask-kelly *job:cleanup` | Same, and N takes T's place in the current Pomodoro |
| `Ask Kelly *job:cleanup *job:send-batch` | N blocks both, in typed order, in one batch |
| `Call registrar &school:transcript *job:apply-x` | Insert between; cycle-checked |
| `*job:cleanup @bob+ask-kelly` | Existing task blocks T (mode `task_dependency`) |
| `Order parts *projects/house/kitchen:cabinets`, `*"Release Plan":publish` | Nested and quoted targets |
| `*job:cleanup` with no other text | Incomplete: needs an owner |
| `X *`, `X *jo`, `X *job:` | Picker open (incomplete) |
| `Fix *urgent* bug`, `Read **Dune**`, `* Buy milk`, `5 * 3`, `R*D` | Literal |
| `X \*job:cleanup` | Literal `*job:cleanup` |
| `Support *nix` (trailing) | Partial; blocks submit with a teaching error (`\*nix`). Zero vault occurrences; accepted. |
| `N *T &T` | Direct cycle; refused, vault untouched |

cld found zero vault task lines with a whitespace token starting with `*`.

## bob-cli implementation

### Lexer and parse

Generalize the `&` spots in `dependencies.rs` into a two-direction scan
(`DependsOn | Blocks`), and apply the [grammar guards](#grammar-contract) to `Blocks`.
Keep a separate `blocked_tasks[]` list on the parsed item; never add a direction flag to
`dependencies[]`, which every consumer reads as "prerequisites". Ownership reuses
`resolve_execution_ownership`, including `@@` inheritance. New additive names:

- spans `blocked_task_sigil`, `blocked_task_note`, `blocked_task_block_id`
- need/context `blocked_task`, per-item `blocked_tasks[{raw, note, block_id, quoted, range}]`
- reuse need `dependency_target` (no owner) and mode `task_dependency` (existing owner)

Also fix `bob-cli-7m` here: `@cash &foo:bar Buy milk` captures literal text because the
leading run never skips `@…`. `*` would inherit the bug.

### Completion

Add context `blocked_task`, using `capture_dependency_tasks::discover` filtered by
[A8](#explicit-requirement-adjustments). Rank empty queries with today's linked tasks
first (the running entry first), then Pending, then Next, then the same note, then the
rest. Reuse the `&` row shape plus `already_blocked` and a `disabled_reason` (self,
would-cycle, internal `^prj`, duplicate ID). Add `blocked_task_replacement` to
`capture-task-id` for targets without an ID. All changes are additive, so
`schema_version` stays 1, and no new subcommand is needed (`cli_rules`).

### Execution order

One staged batch; nothing is written until the whole draft plans:

1. Resolve, dedupe by identity, and validate every `*` target (A8).
2. Choose N's destination and reserve its block ID (A9).
3. Plan N's own `&` prerequisites (N may be born `[?]`), insert N, and stage N's Task
   Link if `:id` or `#pomodoro` asked for one and N is not Blocked.
4. For each T in typed order, call the shared existing-dependent writer with
   dependent = T and prerequisites = [N]. It merges the Depends-On line and fields,
   stamps T fresh, flips T to `[?]`, handles `^prj` residents and the tag, consumes links
   (A2, A3), transfers commitment (A6), and stages N's BLOCKS line. Re-locate N by block
   ID after each pass, because `locate_new_task_ref` matches exact text that goes stale.
5. Remove only the entries this item emptied (A4).
6. Report `dependency_updates[]`, `consumed_links[]`, removed `pomodoro_blocks`, and N's
   minted ID in a new additive field. Don't reuse `minted_dependent_block_id`, whose name
   means the opposite here.
7. Commit through the existing guarded writer. It provides preimage checks and rollback;
   don't promise cross-process or crash atomicity it doesn't have.

The shared writer needs four changes:

- address the dependent by vault path plus block ID, not a lower-cased route
- consume by identity, with notes preserved
- dependent-side guards
- the Next cap when N is new

Existing-owner `*` items go through the dependency-only path beside
`plan_dependency_only_item`.

### Human output

Example:

```text
✓ Ask Kelly for references!  mac_inbox.md ^ask-kelly-for-references   [*] Next
  🧱 blocks "Do cleanup tasks!"  job.md ^cleanup  [/] → [?] Blocked
  − removed its Task Link from JOB 10:10–10:35 (running) · deleted the empty Pomodoro
```

### Docs and records first

- `docs/capture.md`:
  - a "Blocking existing tasks with '*'" section after the `&` section
  - grammar-table rows and collision rows
- `docs/task-dependencies.md`:
  - a §5 bullet, "Adding a dependency from the prerequisite side", which `bob-cli-3p`
    can share
  - capture `*` added to the writer tables
  - `ST` vectors
  - the PDL7 amendment, if approved
- A decision record via `/sase_memory_write`. It covers the sigil, consume-by-reuse, note
  preservation, the Next cap, and link-then-consume ordering.

### Tests that matter most

- Lexer: the guard vectors, plus `=x*1` and `=*` unchanged.
- Equivalence: `N *T` and the two-item draft produce identical vault diffs, apart from
  the minted ID.
- Nested target with a basename ledger link: consumed.
- Notes under T's link: preserved, and the session survives.
- Running entry emptied: deleted *and reported*.
- An unrelated childless entry is untouched by capture.
- `N @inbox:id *T`: the session survives.
- A `^prj` target blocks residents. An internal `^prj` target is refused.
- Direct, transitive, cross-item, and `&`+`*` cycles are refused with the vault
  byte-identical.
- The Next cap holds when T was `[/]`.
- Automatic IDs work with mirrors on and off.
- A later link gesture in the same batch drops the edge, and the final preview stays
  accurate.
- Dry-run output equals the live run, and a second run is a no-op.

## Bob Mac Capture

The app stays a renderer (`decisions:mac-capture-is-a-thin-client`). The changes are
about S–M:

- **One picker, parameterized by direction.** Route context `blocked_task` and need
  `blocked_task` through the shared dependency handler. Vary the sigil, insertion prefix,
  and copy: header "Blocks · Choose a task to block", row "Becomes Blocked until this is
  done", and "space adds another *". Don't reuse the `&` picker unchanged: its hard-coded
  `&` prefix, or the `dependency_replacement` path in the Add-ID flow, would silently
  reverse the edge.
- Add the three `blocked_task_*` span kinds to the trigger set and the palette. Make
  Backspace on an empty filter accept `*` (byte 42) as well as `&`. The Add-ID flow uses
  `blocked_task_replacement`, and falls back to the existing "This Bob is too old…"
  message.
- Confirm Tab and Shift-Tab precedence: a line-initial `*` stays a bullet placeholder,
  and the trailing-only picker trigger ([grammar contract](#grammar-contract)) keeps the
  two apart.
- **Preview.** Iterate `dependency_updates[]`, falling back to the singular field. Show
  consumed links, preserved-note conversions, and `^prj` resident counts. Show a red line
  for a deleted running session; `removed` `pomodoro_blocks` already render red.
- **Fixtures and tests.** Mirror the `task-dependency-*` fixtures and the
  `DependencyPickerPresentationTests` and `CaptureDependencyPanelTests` suites. Check
  them with `just portable-check`, then macOS typecheck and CI.

## Recommended solution

Ship `*note:block-id` as **`&` with the roles swapped**, as one epic in this order:

1. **Decide and write the contract.**
   - Settle the [open questions below](#open-questions-for-bryan).
   - Write the [docs](#docs-and-records-first), the vectors, and the decision record.
   - File the PDL7 amendment for capture.
2. **Fix the shared consumption path (bob-cli). It also benefits `&`.**
   - Report consumed links and removed entries (`bob-cli-7l`).
   - Match by identity.
   - Preserve notes under consumed links.
   - Remove only entries the capture emptied.
3. **Parse and complete (bob-cli).**
   - Two-direction lexer with the Markdown guards.
   - `blocked_task*` wire names.
   - A picker pool of open tasks only, today's linked tasks first.
   - `blocked_task_replacement`.
   - Fix `bob-cli-7m`.
4. **Execution (bob-cli).**
   - Always assign N's ID.
   - Stage N and its optional link first.
   - Call the path-addressed existing-dependent writer once per target, with the
     commitment transfer capped at Next.
   - Allow existing owners and `&`+`*` together.
   - Emit `dependency_updates[]`.
5. **Bob Mac Capture.**
   - The direction-parameterized picker.
   - The Backspace and Add-ID fixes.
   - Preview cards for every blocked task, consumed link, preserved note, and deleted
     session.
6. **Follow-ups, not v1.**
   - Reconcile parity and plugin (PDG1) parity for note preservation.
   - A picker key that flips `&`↔`*` through `capture-rewrite`.
   - The Obsidian reverse Blocks stage (`bob-cli-3p`) on the same
     `docs/task-dependencies.md` §5 contract.

**Leave alone:**

- Auto-linking N into T's slot.
- The soft-block drop on later link gestures.
- Deleting a running session that has truly emptied, which you asked for. Make it
  visible instead.

**Effort:** bob-cli about M, Mac about S–M (cld's estimate, which I agree with).

### Open questions for Bryan

1. **N's lane (A6):** cap a new blocker at Next (recommended), or strict `&` parity,
   where Pending T makes N `[/]`?
2. **Notes under a consumed link (A3):** approve amending PDL7 so notes survive under a
   plain-text bullet (recommended)? Or refuse the capture when notes exist, or keep
   subtree deletion?
3. **Sigil:** `*` (recommended), or `?`, which mirrors the target's `[?]` and needs no
   emphasis guards?
4. **Existing owners in v1 (A7):** include them (recommended), or new-task owners only?

## About this report

*Lead researcher, 2026-10-14. This report merges four independent reports
([`__cdx`](capture_star_blocks_modifier__cdx.md),
[`__cld`](capture_star_blocks_modifier__cld.md),
[`__grk`](capture_star_blocks_modifier__grk.md),
[`__gem`](capture_star_blocks_modifier__gem.md)) with my own checks. I checked bob-cli at
`23bee1f`, bob-mac-capture at `7e7d8d6`, and the live vault, which I only read. I ran no
new capture probes. The behavior probes cited in this report come from cdx and cld, who
reproduced them independently in throwaway vaults.*
