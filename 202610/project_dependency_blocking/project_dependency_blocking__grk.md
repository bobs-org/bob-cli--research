# Project-task dependency links: frontmatter source of truth, residence-blocked children, and ledger prune

> **Research query:** Add full support to `^prj` tasks for task dep links: store a project-level dependency as `depends_on` frontmatter (not a Depends-On child of `^prj`), cascade Blocked to every task that lives in a blocked project, prune those tasks' Pomodoro Task Links (and empty Pomodoros), update Ctrl+Shift+P, the create-project-from-task keymap, and `bob task reconcile`, and amend the task-dep-link glossary. Critique the plan, call out justified requirement adjustments, and recommend a solution.

## Bottom line

**Build it, with the adjustments below.** The Databricks project note is a real, current failure of the ordinary-task dep-link contract when it is applied to a `^prj` lifecycle task. A project-level dependency belongs in YAML next to `scheduled` and `parent`, ordinary resident tasks should become `[?]` while the project cannot proceed, and those tasks should leave today's ledger.

The idea is good. Three parts of the request as written would create new bugs if implemented naively:

1. Copying a Depends-On line onto every child (or writing inherited `[dependsOn::]` that R2 would then adopt into a line) spreads the ugly format instead of retiring it.
2. Stripping Task Links from newly Blocked Next/Pending children, under today's recovery rules, **destroys the Next lane** when the project unblocks. That is a real GTD cost; it is still the right default, and it should be chosen on purpose.
3. `blocked.md`'s DEPENDENT section queries Tasks `is blocked` (open `dependsOn` ids). Residence-blocked children with no inherited field are `[?]` in the project note and on the dash BLOCKED chip, and invisible in that section.

Recommended design: **project `depends_on` YAML is the source of truth for `^prj`**; derive a hidden `[dependsOn::]` on the lifecycle line for Tasks; **never** give `^prj` a Depends-On child; **derive Blocked from residence** for ordinary open tasks in that note; prune live Pomodoro links as a general blocked-task invariant in both the keymap and `bob task reconcile`.

---

## Verdict

| Question | Answer |
| --- | --- |
| Is this a good idea? | Yes. The current `^prj` dep write is the ordinary-task writer applied to a slot that already has machine-owned children (Sub-projects, schedule/work/cancel logs). |
| Would I take a different approach? | Same destination, stricter mechanics: residence-derived Blocked, no inherited child lines/fields, YAML wikilinks, chips on the `^prj` line, a new decision record that specializes `task-deps-are-depends-on-links` for project notes. |
| Vault blast radius today | One project (`job_apply_to_databricks.md`), two Next children, two live JOB-pomodoro links. 86 project notes, 0 existing `depends_on` keys, 40 ordinary-task Depends-On lines in project notes that stay as they are. |

---

## Is this a good idea

**Yes.** Evidence from the live vault and the current contracts:

### The Databricks note is the bug, not a style nit

`~/bob/job_apply_to_databricks.md` today:

```markdown
---
parent: "[[job]]"
template: "[[new_project]]"
type: "[[project]]"
status: wip
---
- [?] #task #prj Apply to DataBricks NYC role(s)! … #hide [dependsOn:: job__update-linkedin] ^prj
	- ⛓️ **DEPENDS ON:** [[job#^update-linkedin]]

## Tasks
### Next & In Progress
- [*] #task #ref [[ref/chat/databricks_nyc_cv_and_role_pitches|…]] ^ref-databricks-nyc-cv-and-role-pitches
- [*] #task #ref [[ref/chat/databricks_nyc_cv_and_role_pitches_v2|…]] ^ref-databricks-nyc-cv-and-role-pitches-v2
```

Three failures sit on one note:

1. **The project is blocked; the work is still Next.** Today's open JOB pomodoro still carries both CV Task Links (`2026/20261012.md` lines 43–44), next to `[[job#^update-linkedin]]`. Dash still offers those rows as doable work.
2. **The Depends-On child occupies the `^prj` first-child slot.** `bob projects sync` already owns that slot for `🧩 **Sub-projects:**`. The dep-link contract says the Depends-On line is the first direct child (or second if a Cancel Log exists). Those two machine lines cannot share one first-child rule. This is why a "sub-sub-bullet" under `^prj` feels wrong: it is fighting Sub-projects, schedule logs, and work logs for the same indent.
3. **`^prj` is `#hide`, so blocked.md never shows the project-level wait.** `blocked.md` filters `!task.tags.includes("#hide")`. The only `[?]` line is hidden. The children are `[*]`, so they miss `is blocked` too. The dependency is invisible on the Blocked page.

Bryan is already in the middle of this: `job.md` has `[/] Re-organize [[job]] using dependencies and sub-projects!`, and today's closed BOB pomodoro logged `[[bob#^project-task-dependencies]]`.

### The `scheduled` analog already exists and works

`docs/projects.md` "Scheduling from the `^prj` task":

- Cursor on `^prj` + Task Card **Schedule** writes YAML `scheduled: YYYY-MM-DD`, strips inline `[scheduled::]` from `^prj`, propagates to ordinary open tasks, derives `[?]` in the same editor transaction, and prunes Pomodoro links for every ordinary task that received a future date **plus `^prj` itself**.
- `dependsOn` is explicitly called out as **not** a project property: "it is derived from the task's Depends-On line, never written by hand."

The request is: give `depends_on` the same project-property status `scheduled` already has, with Blocked cascade for **every** project-blocked reason, not only a future date.

That analog is the right one. A future-scheduled project already blocks children via `[scheduled:: P]`. A dep-blocked project has no equivalent, which is why Databricks children stayed Next.

### Convert-from-task would make it worse

`buildProjectSeedFromChildBullets` (`bob-navigation-hotkeys` `src/110-project-seed.js`) classifies `^prj` children as managed logs, ALL-CAPS sections, or **tasks**. A Depends-On line is a non-checkbox bullet, so `buildProjectTaskLineFromChildBullet` would seed:

```markdown
- [ ] #task ⛓️ **DEPENDS ON:** [[job#^update-linkedin]] [created::YYYY-MM-DD]
```

`parseProjectSourceTaskLine` strips `scheduled`, priority, `#task`, and the trailing block id. It does **not** strip `[dependsOn::]` or `[id::]`, so those fields would also land in the `^prj` description.

The create-project-from-task keymap (`bob-navigation-hotkeys:create-project-note-from-task`, bound as **Alt+Ctrl+Shift+N** / docs `<ctrl+shift+option+n>`; the request's `<cmd+ctrl+shift+n>` is this command) has to learn `depends_on` or conversion of a sequenced task is lossy or garbage.

### Ordinary task deps in project notes are fine

A vault pass over 86 project notes found **41** Depends-On lines; **40** of them sit on ordinary `#task` rows (`sase_model.md`, `sase_gate.md`, …). Those stay on the managed first-child line. Only the `^prj` line is the special case.

---

## Requirement adjustments

| # | You asked | I recommend | Why |
| --- | --- | --- | --- |
| **ADJ-1** | Store the dep as `depends_on` frontmatter, not a Depends-On child of `^prj` | YAML list of shortest unambiguous wikilinks is the source of truth. Derive `[dependsOn::]` on the `^prj` line (CSS-hidden, Tasks index). Delete any Depends-On child under `^prj`. | Matches `parent` / `scheduled`. Links rename with the note; ids do not. Tasks `is blocked` still reads `[dependsOn::]`. R2 must **not** adopt a line from that field on `^prj` (see ADJ-2). |
| **ADJ-2** | Reconcile auto-fixes the Databricks note | New R-prj rules, **before** ordinary R1–R10: adopt a `^prj` Depends-On line or orphan field into YAML, then delete the line. Frontmatter wins; union in missing line targets during the first adopt. Ordinary tasks in the same note keep R1–R10. | One-file migration today. Without the R2 exception, a derived `^prj` field would grow a new Depends-On child on the next run. |
| **ADJ-3** | Any task that lives in a blocked project is blocked | **Residence only** (the project note that holds the checkbox). Open ordinary `#task` lines in that file become `[?]`. Do **not** cascade through `parent` to sub-project notes. Do **not** copy the project's deps onto children as lines or `[dependsOn::]` fields. | Sub-projects are independently pullable work. Inherited fields would R2-adopt a Depends-On line onto every child. "Lives in" is the glossary residence rule already. |
| **ADJ-4** | "Whenever a project is blocked" | Define **project-blocked** as: unmet `depends_on` YAML **or** a future `scheduled:` date. `status: waiting` and "a child is `[?]`" are not project-blocked. `^prj` itself becomes `[?]` for unmet YAML deps; for a future schedule it stays the current `#hide` contract (no inline date on `^prj`). | Schedule already cascades via `[scheduled::]`. Deps are the missing reason. Over-broad cascade (ancestry, waiting, any-child-blocked) would freeze whole trees. |
| **ADJ-5** | Blocked tasks should not have Task Links; empty Pomodoros go away | Make this a **vault-wide blocked-task invariant**, implemented in Ctrl+Shift+P immediately and in `bob task reconcile` authoritatively. Reuse the existing deferral prune (dedicated bullet + subtree, else token-only; struck/closed entries untouched) and the existing empty-Pomodoro cleanup. | Today only a **future `scheduled`** prune exists, and only in the picker. Hand-edited YAML and dep-blocked tasks keep links. Reconcile already deletes canceled links and empty Pomodoros; blocked-link prune is the missing sibling. |
| **ADJ-6** | (implicit in ADJ-5) | **Accept Next/Pending lane loss** on project-block. When the project unblocks, children recover per existing rules: Ready unless still linked or recently active. Successor-linking does **not** dump every resident task into the pomodoro (extend SL11: `^prj` stays recover-only; children recover, Bryan pulls). Follow-up, not this change: reopen `task-lanes-are-sticky` and make Blocked an overlay. | Sticky-lanes already say "Lanes don't survive Blocked" and store no previous-status. Linking a blocked child to preserve Next contradicts ADJ-5. Auto-linking every child on unblock would dump a 10-task project onto today. |
| **ADJ-7** | Update Ctrl+Shift+P | On `^prj` (and on a leftover Depends-On child of `^prj`), the Depends on stage reads/writes YAML. Same transaction: derived `[dependsOn::]`, `[?]` on `^prj` + ordinary open residents, prune links, promote open prerequisites to at least the strongest lane among `^prj` and those residents, regroup `## Tasks`. Ordinary tasks in the note keep the line writer. Ctrl+D on project `depends_on` clears the key (scheduled analog); surgical add/remove stays on the stage. | The scheduled picker already does a multi-file transaction (project note + daily prune + child fields). |
| **ADJ-8** | Update create-project-from-task | Command id `create-project-note-from-task`. Forward: strip `[dependsOn::]`/`[id::]` from the source description; parse a source Depends-On child (and field ids) into YAML `depends_on`; never seed that child as a `## Tasks` row. Reverse: skip machine `🧩 **Sub-projects:**` children; synthesize a Depends-On **line** on the restored ordinary task from YAML (the restored row is no longer `^prj`). | Reverse conversion is how a project becomes an ordinary task again, so the line is the correct ordinary-task form. |
| **ADJ-9** | (omitted in the request) | **Show** project deps: Obsidian properties pane (clickable wikilinks) **and** the existing live chips drawn on the `^prj` line from YAML. Empty YAML key is omitted. | Moving the SoT into YAML without a Live Preview host hides the wait. Chips already exist for ordinary Depends-On lines (`docs/task-dependencies.md` §11.5). |
| **ADJ-10** | Update the glossary term | Amend `glossary:task-dependency-link` and write a **new** decision `project-deps-are-frontmatter`. Do not edit `task-deps-are-depends-on-links` in place; mark it partly superseded. Also update `docs/task-dependencies.md`, `docs/projects.md`, `docs/task-status-hooks.md`. | Decision records are immutable once accepted. The line remains SoT for ordinary tasks. |
| **ADJ-11** | (omitted) | Update `blocked.md` DEPENDENT from bare `is blocked` to the dash chip's disjunction: `(is blocked) OR (status.name includes Blocked)`, still excluding `#hide`. Optionally group project-residence rows under their path (already `group by path`). | Dash BLOCKED already uses that OR (`dash.md` lines 89–94). Live `blocked.md` DEPENDENT would miss residence-blocked children that have no `[dependsOn::]`. The Tasks-parity fixture already uses the OR. |
| **ADJ-12** | (omitted) | Capture: a new or edited ordinary task **in a blocked project** lands `[?]` and is not linked. `@route^id+` project constructions still reject `&` (keep that); adding a project dep is an Obsidian/`bob task reconcile` gesture on `^prj`. Ctrl+Shift+M **into** a blocked project applies the same cascade+prune as the picker. | Otherwise capture and move recreate the Databricks shape between 15-minute reconcile runs. |

---

## How it works today

### Ordinary task deps (unchanged)

`decisions:task-deps-are-depends-on-links` and `docs/task-dependencies.md`:

- SoT is the first-child line `⛓️ **DEPENDS ON:** [[#^a]] • [[note#^b]]`.
- `[dependsOn::]` / `[id::]` are a derived Tasks index (R1–R10 in `bob task reconcile`).
- Blocked `[?]` while any prerequisite is open (AND, finish-to-start) or `scheduled` is strictly after today.
- Linking a dependent under today's open Pomodoros promotes open prerequisites; closing a dependent never closes them.
- Ctrl+Shift+P → `b` (Depends on stage) is the editor.

### Project notes

`docs/projects.md` + glossary `project-task` / `project-note`:

- One `#task … ^prj` completion-criteria row. `#prj` is additive.
- YAML: `type: "[[project]]"`, `parent`, `status`, optional `scheduled`, `project_name_aliases`, counts.
- `bob projects sync` writes status, `#hide`, Sub-projects, and propagated `[scheduled::]`. **It does not write checkboxes.**
- Future `scheduled: P` → every ordinary open task gets `[scheduled:: P]` unless it already has a later date; `^prj` gets `#hide` and never an inline date.
- Sub-projects line is machine-owned, nested directly under `^prj`.
- Convert-from-task moves `scheduled` into YAML; managed logs stay under `^prj`; other children become `## Tasks` or sections.

### Blocked derivation and the ledger

`docs/task-status-hooks.md`:

- Blocked is derived: open `dependsOn` **or** future inline `scheduled`.
- Project YAML `scheduled` participates **indirectly** after sync/picker propagation.
- Reconcile prunes duplicate Pomodoro lines, canceled-task bullets, completed-reference retirement, and **empty Pomodoros**. It does **not** prune links to Blocked tasks.
- The picker prunes links only when a gesture leaves a **future `scheduled`** date (`docs/projects.md` "Deferring a task prunes it from today's open Pomodoros").

### Dash vs blocked.md

- Dash BLOCKED chip: `t.isBlocked(all) \|\| t.status.name.includes("Blocked")` (`dash.md`). `[?]` counts even without `dependsOn`.
- `blocked.md` DEPENDENT: Tasks query `is blocked` only. Tasks `isBlocked()` is "open `dependsOn` id matches an unfinished task" (`src/native/dataview/tasks/js.rs`, `index.rs` `apply_dependencies`). A `[?]` with no `dependsOn` is absent from DEPENDENT and, without a future date, absent from the scheduled sections too.

### Successor links

`docs/task-dependencies.md` SL11: a dependent that **is `^prj` or `#hide`** recovers only; it is not linked into the predecessor's pomodoro slot. That already matches "don't dump the project lifecycle task onto today."

---

## Design forks I considered

### Fork A — Where the project dep lives

| Option | Verdict |
| --- | --- |
| A1. Keep a Depends-On child under `^prj`, only cascade Blocked | Rejected. Solves the Next-children bug, leaves the Sub-projects collision and convert-from-task garbage task. |
| A2. YAML `depends_on` of **ids** (`job__update-linkedin`) | Weaker. Matches the hidden field, fails rename, fails the properties pane. |
| A3. YAML `depends_on` of **wikilinks** (recommended) | Same SoT shape as the ordinary line (links, derived ids). Properties pane is the fallback view. |
| A4. Copy the line onto every ordinary child | Rejected. The thing the request calls unintuitive, multiplied. |

**Pick A3.** Writer form:

```yaml
depends_on:
  - "[[job#^update-linkedin]]"
```

A single scalar `"[[job#^update-linkedin]]"` is accepted (same dual form as `project_name_aliases`). Order is append-only, never re-sorted. Omit the key when empty. Shortest unambiguous link form from `docs/task-dependencies.md` §3, including explicit `done/` paths.

### Fork B — How children become Blocked

| Option | Verdict |
| --- | --- |
| B1. Write inherited `[dependsOn::]` + line on every child | Rejected. R2 adopts lines; merge/unmerge with the child's own deps is a new data model. |
| B2. Write inherited `[dependsOn::]` **without** a line, special-case R2 | Fragile. Inherited vs owned ids are indistinguishable after a hand edit. |
| B3. Residence-derived `[?]` with no child fields (recommended) | One new Blocked reason in reconcile and the picker. Child-owned deps stay on the child's own line. |
| B4. Child depends on same-note `^prj` | Wrong semantics: that waits on **project completion**, not on the project becoming unblocked. |

**Pick B3.** Blocked reasons become:

1. Own open `dependsOn` (line-projected), or
2. Own future `scheduled`, or
3. Containing project note is project-blocked (ADJ-4).

Recovery still uses the existing derived rank once every reason is gone. A child with its own remaining dep stays `[?]`.

`bob projects sync` still does not write checkboxes. The picker applies (3) immediately; reconcile is the vault-wide source of truth, same split as today.

### Fork C — Task Links on Blocked tasks

Today, linking a `[?]` dependent is a supported way to promote its prerequisites (`docs/task-dependencies.md` §5 Promotion). The request retires that.

Replacement promotion paths, already implemented for other gestures:

- Adding a dep to a Next/Pending dependent already raises the target (`getDependencyPromotionStatus`).
- Extend that: adding a **project** dep raises each open YAML target to at least the strongest lane among `^prj` and the note's ordinary open tasks.
- After that, Bryan links the **prerequisite** (LinkedIn) if it is not already on the ledger. In the live example it is already `[/]` and already linked in the JOB pomodoro.

Successor-linking on close is what puts work back on the ledger. For project deps, link nothing automatically except what SL11 already allows (recover `^prj` / `#hide` without linking). Children return to Ready and are pulled with `^^` / Alt+N / capture `!` as usual.

**Pick: prune all live open-Pomodoro links to any task that is Blocked after the run**, project-residence or otherwise. That is slightly broader than "children of blocked projects," and it matches the request's "keep in mind" wording. The Databricks JOB pomodoro keeps LinkedIn, the CV redesign, and the re-organize-job row; it loses the two CV links; it does not become empty.

### Fork D — Blocked as an overlay so lanes survive

`task-lanes-are-sticky` reopen condition: "Lanes must survive Blocked (then Blocked becomes an overlay)." That would preserve Next across a project-block. It is a policy change for **every** Blocked reason, not just projects, and it needs a stored or reconstructed pre-block lane.

**Do not take D in this change.** Call it out as the follow-up if losing Next on Databricks's two CV tasks feels wrong in the first week of use.

---

## Recommended solution

**Treat a `^prj` dependency as a project-note property, modeled on `scheduled`, with residence-derived Blocked and a general blocked-task ledger prune.**

### 1. Source of truth

- Ordinary `#task`: Depends-On line, as today.
- `^prj` in a `type: "[[project]]"` note: YAML `depends_on` list of wikilinks.
- Derived on `^prj` only: `[dependsOn:: id, id]` in Tasks field order, hidden by existing CSS.
- Forbidden under `^prj`: a `⛓️ **DEPENDS ON:**` child. Cancel log, work log, schedule log, and Sub-projects keep their current slots.

### 2. R-prj reconciliation (`bob task reconcile`)

Run before ordinary R1–R10, only on notes whose frontmatter `type` is project and whose unique lifecycle task is `^prj`.

| # | Situation | Resolution |
| --- | --- | --- |
| P1 | Well-formed YAML | `[dependsOn::]` on `^prj` := resolved ids in YAML order. Targets without `[id::]` get one. Delete a Depends-On child if present (after P2). |
| P2 | Line or field present, YAML missing/partial | Adopt resolved line links (then remaining field ids) into YAML in that order, then P1. |
| P3 | YAML link does not resolve | Same heal/breadcrumb behavior as R3/R4; it never blocks. |
| P4 | Empty YAML / empty after removals | Omit the key; remove `[dependsOn::]` from `^prj`. |
| P5 | Ordinary tasks in the same note | Unchanged R1–R10. |

Then:

- **Blocked derivation** adds reason (3): ordinary open `#task` in a project-blocked note → `[?]`. Terminal statuses untouched. `^prj` `[?]` from its own derived field (unmet YAML deps) as today.
- **Ledger prune:** after the post-rewrite graph is known, remove live (non-struck) open-Pomodoro Task Links whose resolved target is Blocked, using the deferral prune's dedicated-bullet vs token rule. Then run the existing empty-Pomodoro cleanup so a pomodoro that lost its last child disappears in the same invocation.
- Report new JSON: `project_dependency_updates`, `residence_blocked`, `removed_blocked_pomodoro_links` (plus the existing `removed_empty_pomodoros`).

The Databricks note after one live run:

```yaml
depends_on:
  - "[[job#^update-linkedin]]"
```

```markdown
- [?] #task #prj Apply to DataBricks NYC role(s)! … #hide [dependsOn:: job__update-linkedin] ^prj

## Tasks
### Blocked
- [?] #task #ref [[ref/chat/databricks_nyc_cv_and_role_pitches|…]]
- [?] #task #ref [[ref/chat/databricks_nyc_cv_and_role_pitches_v2|…]]
```

JOB pomodoro loses the two CV links. LinkedIn stays.

### 3. Ctrl+Shift+P

- Task Card `b` on `^prj` opens the existing Depends on stage, titled as the project note.
- Commits write YAML via `processFrontMatter` (or a guarded full-note transaction that also updates `[dependsOn::]`, checkboxes, and grouping), then prune, then promote prerequisites.
- A leftover Depends-On child under `^prj` is an alias entry point for the same stage (edits YAML, lets reconcile delete the child).
- Counted sessions that mix `^prj` with ordinary tasks: apply YAML rules only to `^prj` targets and line rules to the others, or refuse mixed `b` with a one-line notice. Prefer refuse; mixed meaning is unclear.
- Ctrl+D on the project-backed `depends_on` row clears YAML and recovers children that have no remaining own reason, same recovery snapshot pattern as `deleteProjectNoteScheduledValue`.

Immediate feedback stays with the keymap; reconcile remains authoritative (`decisions:task-status-is-derived`).

### 4. Create / restore project note

Forward (`create-project-note-from-task`):

1. Parse source Depends-On child + `[dependsOn::]` into a wikilink list.
2. Strip those fields from the description used as completion criteria.
3. Exclude the Depends-On child from `buildProjectSeedFromChildBullets` (treat it like a managed log that is **not** inserted under `^prj`; it becomes YAML instead).
4. `applyProjectCreationFrontmatter` gains `depends_on` next to `scheduled`.

Reverse (`convertProjectNoteToTask`):

1. Skip `🧩 **Sub-projects:**` children (machine-owned; copying them is a pre-existing footgun).
2. Skip any leftover Depends-On child.
3. If YAML `depends_on` is non-empty, emit one canonical Depends-On line under the restored ordinary task and the matching `[dependsOn::]` field.

### 5. Visibility

- ledger-tools chips on the `^prj` line, same DC1–DC12 vectors, sourced from YAML (metadataCache + open buffer overlay).
- Properties pane shows the list as links.
- Project note `### Blocked` grouping already moves `[?]` children (`bob:task-status-group:v1:blocked`).

### 6. Other surfaces that must move in the same change

| Surface | Change |
| --- | --- |
| `blocked.md` DEPENDENT | `(is blocked) OR (status.name includes Blocked)` |
| Capture into a blocked project | New ordinary tasks start `[?]`, no pomodoro link |
| Ctrl+Shift+M into a blocked project | Cascade + prune in the move transaction |
| Cycler successor index | Project YAML deps do not auto-link every resident task (SL11 analog) |
| `bob projects list` | Optional: show `blocked by deps` without writing checkboxes |
| `bob capture` `&` on `@route^id+` | Keep rejected; project deps are an Obsidian/`reconcile` gesture |

`bob projects sync` stays off checkboxes and off `depends_on` (user-owned YAML, like `parent`). It may rewrite Sub-projects without touching YAML deps.

### 7. Memory and docs

Glossary `task-dependency-link` (draft amendment):

> A plain (never transcluded) Task Link to a prerequisite. On an ordinary task, dep links sit on the Depends-On first-child line, which is the source of truth for `[dependsOn::]` / `[id::]`. On a project-note `^prj` task, dep links sit in the note's `depends_on` frontmatter (a YAML list of those same Task Links); Bob derives `[dependsOn::]` on `^prj` and never writes a Depends-On child there. An ordinary open task that lives in a project-blocked note is itself Blocked. Blocked tasks do not keep live Pomodoro Task Links.

New decision `project-deps-are-frontmatter`: claim, `scheduled` analog, residence cascade, prune invariant, R-prj, cost (fourth parser special case, Next-lane loss, blocked.md query). Partly supersedes `task-deps-are-depends-on-links` for `^prj` only.

### 8. Implementation order

1. Contract: `docs/task-dependencies.md` (R-prj + residence Blocked + prune), `docs/projects.md` (property table next to Schedule-from-`^prj`), `docs/task-status-hooks.md`. Shared vectors first.
2. `bob task reconcile` (Rust): R-prj, residence Blocked, blocked-link prune, reports. This alone auto-fixes Databricks once shipped to the MacBook hooks timer.
3. bob-navigation-hotkeys: YAML writer, picker prune reuse, convert forward/back, mixed-session refuse.
4. ledger-tools: `^prj` chips from YAML.
5. Vault `blocked.md` query; cycler successor guard; capture/move hooks.
6. Glossary + decision via `/sase_memory_write`.
7. Tests: Rust R-prj / residence / prune; JS convert + picker; Tasks-parity blocked query; one fixture cloned from Databricks.

Do not migrate YAML by hand. One reconcile run is the migrator.

---

## What I would not do

- **Do not** give area notes a `depends_on` key. Areas have no `^prj` and no done state.
- **Do not** treat `^ref` like `^prj`. Reference-task deps stay on the line unless a later request says otherwise.
- **Do not** propagate project deps into child `[scheduled::]`-style fields. Schedule is a date the child can independently postpone; a dep is a graph edge whose visible home is the project.
- **Do not** change `bob projects sync` to write `[?]`. Checkbox ownership stays with reconcile and the keymap.
- **Do not** walk ancestry via `parent`. A blocked parent project leaves sub-project notes pullable.

---

## Risks

| Risk | Mitigation |
| --- | --- |
| Next CV tasks become Ready after LinkedIn closes; Bryan has to re-pull them | ADJ-6, chosen on purpose. Overlay follow-up if it hurts. |
| `blocked.md` DEPENDENT empty for residence-blocked children | ADJ-11 in the same change. |
| R2 re-creates a `^prj` Depends-On child from the derived field | P1/P2 before R1–R10; test vector: field present, YAML present, no line, second run is a no-op. |
| Sub-projects vs leftover line during rollout | Reconcile deletes the line in the same run it writes YAML. |
| 15-minute window if only reconcile ships | Ship picker + reconcile together; MacBook hooks remain the backstop. |
| Tasks `is blocked` is "load-bearing" (`task-deps-are-depends-on-links` reopen) | `^prj` keeps a derived field, so the project row stays `is blocked`. Children rely on status name `[?]` plus ADJ-11. Document that `is blocked` is no longer the only Blocked query. |
| Convert reverse copies `🧩 **Sub-projects:**` onto the restored task | Skip that marker in the same convert patch (ADJ-8). |

---

## Live census (2026-10-12)

| Fact | Count / example |
| --- | --- |
| Project notes | 86 |
| YAML `depends_on` already present | 0 |
| `^prj` with a Depends-On child | 1 (`job_apply_to_databricks.md`) |
| `^prj` checkbox `[?]` (true lifecycle line) | 1 (same file) |
| Ordinary Depends-On lines inside project notes | 40 |
| Projects with YAML `scheduled` | 14 (1 future; 0 open children there) |
| Open ordinary tasks in the dep-blocked project | 2, both `[*]` |
| Live open-Pomodoro links to those two | 2, under `— JOB` in `2026/20261012.md` |
| Open `[?]` tasks vault-wide | 403 (384 future-scheduled, 30 with `dependsOn`, 0 with neither) |

The feature is small in vault terms and large in contract terms: one note to fix, many writers to keep in sync.

---

## Recommended rollout check

After picker + reconcile land, on the real vault:

1. `bob task reconcile --dry-run` names `job_apply_to_databricks.md` for YAML adopt, line removal, two residence `[?]` flips, two JOB-pomodoro link removals, and no empty-Pomodoro deletion (JOB still has three other children).
2. Live reconcile is idempotent on a second run.
3. Ctrl+Shift+P `b` on that `^prj` shows LinkedIn in CURRENT; removing it recovers the two CV tasks to Ready (unlinked) and omits `depends_on`.
4. Convert a sequenced ordinary task to a project and back: YAML appears, no garbage `## Tasks` row, reverse restores a Depends-On line on the parent note.

---

## About this report

- **Researcher:** grk (independent swarm member). No peer reports from this swarm were read.
- **Snapshot:** bob-cli workspace `bob-cli_14`; bob-plugins linked checkout; vault `~/bob` including `job_apply_to_databricks.md` and `2026/20261012.md`.
- **Audited memory:** `glossary:prj task`, `glossary:task dep link`, `glossary:prj note`, `glossary:task block link`, `glossary:Pomodoro`, `glossary:Area Note`, `glossary:ref task`, `glossary:freshness`, `glossary:inbox note`; `decisions:task-deps-are-depends-on-links`, `decisions:task-status-is-derived`, `decisions:task-lanes-are-sticky`, `decisions:today-is-read-from-the-ledger`, `decisions:ready-is-freshness-gated`, `decisions:review-walk-is-tiered`; `sase_artifacts.md`, `cli_rules.md`.
- **Prior research (unrelated epic, audited):** `research:202610/task_dep_link_depends_on_line/task_dep_link_depends_on_line.md`.
- **Scope:** research only. No code, vault note, config, or memory file was changed.

## Sources

**bob-cli**

- `docs/task-dependencies.md` (grammar, R1–R10, §5 semantics, SL11)
- `docs/projects.md` (YAML `scheduled`, Schedule-from-`^prj`, deferral prune, convert-from-task)
- `docs/task-status-hooks.md` (Blocked derivation, empty Pomodoros, canceled-link cleanup)
- `docs/dashboard.md`, `docs/capture.md` (`&` rejects project constructions)
- `src/native/task_status_hooks/` (reconcile, structure prune)
- `src/native/dataview/tasks/index.rs` `apply_dependencies`, `js.rs` `isBlocked`
- `src/native/projects/mod.rs` (Sub-projects marker)
- `src/native/task_complete/successors.rs` (dependents from `depends_on` fields)

**bob-plugins**

- `plugins/bob-navigation-hotkeys/src/110-project-seed.js` (`buildProjectSeedFromChildBullets`, `applyProjectCreationFrontmatter`)
- `src/100-yank-and-paths.js` (`parseProjectSourceTaskLine`, `buildProjectTaskLineFromChildBullet`)
- `src/210-rename-and-line-context.js` (`parseProjectNoteFrontmatter`, `splitProjectNoteForReversal`, `getProjectReversalChildLines`)
- `src/260-project-schedules.js` (YAML scheduled write/delete + child recovery)
- `src/660-plugin-project-notes.js` (create from task / convert to task)
- `src/500-plugin-transclusion-and-link-picker.js` (`readDeferredPomodoroSnapshot`)
- `plugins/bob-ledger-tools` (unblocked glyph / dash collections; chips host)

**Vault**

- `~/bob/job_apply_to_databricks.md`
- `~/bob/job.md` (`^update-linkedin`, re-organize-job)
- `~/bob/2026/20261012.md` (JOB pomodoro)
- `~/bob/blocked.md`, `~/bob/dash.md`
- `~/bob/_templates/new_project.md`
- `~/bob/.obsidian/hotkeys.json` (`create-project-note-from-task` = Alt+Ctrl+Shift+N)

**Memory**

- `glossary:task-dependency-link`, `glossary:project-task`, `glossary:project-note`, `glossary:task-link`
- `decisions:task-deps-are-depends-on-links`, `decisions:task-status-is-derived`, `decisions:task-lanes-are-sticky`
