# Task dep links: from transcluded sub-tasks to one Depends-On line

- **Researcher:** cld (one of five independent reports in this swarm; no peer report, transcript, or summary was
  consulted).
- **Snapshot:** Fri 2026-10-02. bob-cli `81b45eb`; bob-plugins `ede89d3` (navigation-hotkeys 1.50.0,
  task-status-cycler 1.19.0, block-id-prompt 1.17.0, ledger-tools 1.17.0); vault numbers from read-only `bob query`
  against `~/bob`, plus the `gh:bobs-org/bob` checkout at `5b54444e`.
- **Question:** Should the vault stop using transcluded task links as dependency sub-bullets and switch to plain task
  links, all on one line? How should adding and removing dependencies on any vault task work from `<ctrl+shift+p>`,
  with vault-wide fuzzy search? What should the new "task dep link" glossary term say? Is the plan sound, what would
  I change, and what should be built?
- **Scope:** research only. No code, vault note, memory file, or config was changed.

## Bottom line

**Yes, build it. It removes the worst parts of the current design. But "plain links on one line" is only the
visible part. To make it reliable, intuitive, and beautiful, four decisions have to come with it.**

1. **The Depends-On line is the source of truth.** A task's dep links live on one managed first-child line:
   `⛓️ **DEPENDS ON:** [[#^a]] · [[note#^b]]`.
   - `[dependsOn::]` and `[id::]` stay, but only as a projection computed from that line. Every writer updates them
     in the same transaction, and `bob task-status-hooks` repairs any drift across the vault.
   - Your own vault CSS already describes these fields as "derived deterministically (block id and transcluded
     block links)", so the line is the authority you already have in mind.
2. **The real usability fix is the picker, not the line format.** Today the Ctrl+Shift+P `dependsOn` picker only
   lists tasks **in the current note**.
   - That is almost certainly why 44 of the vault's 45 dependency edges are same-note.
   - A vault-wide stage with Rust-compatible fuzzy ranking, toggle semantics, and a cycle guard is what makes
     cross-note dependencies easy.
3. **"Beautiful" needs a renderer, not just a text format.** Unaliased block links render as `^id` noise, and stored
   aliases go stale. A ledger-tools Live Preview / Reading view decoration should draw each dep link as a status chip
   with the target's live description.
4. **Dependencies are prerequisites, not sub-tasks.** Today's transclusions mix the two.
   - Closing an *embedded* dependent can recursively force-close its prerequisites.
   - `#^ref` reading-task embeds are silently treated as dependency edges.
   - With dep links as their own construct, both side effects go away on purpose.

**I am changing your requirements in nine places.** Each is called out as **ADJUSTMENT A1–A9** where it applies, and
summarised in [§10](#10-recommended-solution).

---

## 1. How dependencies work today

### 1.1 Two representations, read by different consumers

A dependency is currently written twice:

```markdown
- [?] #task Make appt w/ Rahway Hospital for CT scan! … [id:: body__rahway] [dependsOn:: body__hospital-swarm] ^rahway
	- ![[#^hospital-swarm]]
```

| Consumer | Reads the transcluded child `![[…#^id]]` | Reads `[dependsOn::]` / `[id::]` |
| --- | --- | --- |
| `bob task-status-hooks`: rank propagation (Pomodoro roots → deps → Next / In Progress) | **yes**. A sole embed that is a direct child (`references.rs:307–516`) | no |
| `bob task-status-hooks`: derived Blocked `[?]` | no | **yes** (`sync.rs:678–737`) |
| `bob capture =x`: embedded tree close | **yes**. Every embed anywhere in the closed task's block, recursively (`capture_pomodoro_close/linked_tasks.rs:540–620`, `1189–1203`) | warning only |
| Tasks plugin, `dash.md`, `blocked.md`, ledger-tools lanes, Rust lane queries | no | **yes** (`is (not) blocked`, `task.isBlocked`) |
| task-status-cycler: Pomodoro tree close, Ctrl+Enter on embeds | **yes** (`main.js:2597`, `9941`) | – |
| task-status-cycler: retire on close, restore on reopen | **yes**. Strikes `![[…]]` → `~~[[…]]~~` and restores the `!` on reopen (`4621–4760`) | – |
| task-status-cycler: Blocked recovery, id normalizer, rename | no | **yes** (`4468`, `6167–6186`, `6588`) |
| block-id-prompt: refuse Ctrl+Shift+Enter on dep embeds; picker Blocked chips | **yes** (`2878–2900`) | **yes** (`1019–1047`) |
| navigation-hotkeys: Ctrl+Shift+P picker, `!`, consolidate, Ctrl+Shift+M | both | both |
| vault CSS `dataview-properties.css` | – | hides `[id::]`; collapses `[dependsOn::]` to a link glyph |

Two different graphs answer two different questions:

- **"Is this task Blocked?"** is answered from the fields.
- **"Which tasks get promoted, or closed, with this one?"** is answered from the embeds.

They agree only as long as every writer keeps them in sync.

### 1.2 The writers disagree with each other

A code survey of `bob-navigation-hotkeys/main.js` and the other plugins found these inconsistencies:

- **Two ways to add a dependency, with different side effects.**
  - The **Ctrl+Shift+P picker** writes the field and the embed (`setLocalTaskDependency` 31371,
    `executeDependencyBatch` 23167). It never marks the parent `[?]` and never promotes the target.
  - The **`!` toggle** does both (`applyDependencyAwareTransclusionChanges` 25413).
- **The picker only sees the current note.**
  - Candidates come from the active editor buffer (`showLocalTaskValueStage` 22240 → `getOpenLocalTasks` 1155). The
    empty state reads "No open tasks in this file".
  - The config comment defines `local_task_id` as "an open #task chosen from the current file".
  - Matching is an unscored subsequence test (`fuzzyMatchesText` 14348), so results stay in document order.
  - Cross-note dependencies never appear as candidates, so they can't be removed one at a time from the picker.
- **Plain Enter on an existing dependency does nothing useful.** It re-upserts and reports "Already depends on X".
  Removal requires Tab-marking, `!`, or Ctrl+D.
- **Ctrl+D on `dependsOn` deletes only the field** (31490–31588). The embeds are orphaned and the parent stays `[?]`.
- **The "Rewrite dependency navigation links" command can delete cross-note embeds.** Its lookup table covers only
  the current note's tasks (26045–26066). The survey reproduced this in memory.
- **Task Link mode hides `dependsOn` completely** (`createLinkPickerPropertyItems` 15382). Its comment reads: "remote
  tasks are edited through their own notes, never via dependency transclusion." One reason is that a dependency embed
  `- ![[#^dep]]` *is syntactically a Task Link bullet*.
- **Picker writes are several separate editor replacements**, so one gesture can take several undo steps. The counted
  path and `!` are single transactions.

None of these is a format problem. They come from having **two representations, no single authority, and several
writers**. Switching to plain links on one line fixes none of them unless the authority question is settled. That is
the core of this report.

### 1.3 Vault census (2026-10-02)

| Measure | Count |
| --- | ---: |
| Tasks with `[dependsOn::]` (outside daily notes) | **44** across 18 notes |
| …with 1 dependency / 2 dependencies | 43 / 1 |
| …open parents (all `[?]`) / closed parents | 14 / 30 |
| Dependency edges same-note / cross-note | **44 / 1** |
| Dependency child bullets: live embeds (same / cross) | 38 (34 / 4) |
| Dependency child bullets: struck retired `~~[[…]]~~` | 5 |
| `dependsOn` tasks with no child bullet | 2 (both closed) |
| Sole-embed children under tasks **without** `dependsOn` | 21, all `#^ref` reading-task embeds |
| Tasks with `[id::]` | 80 |
| Open tasks vault-wide (picker pool) | 844 in 278 notes: 620 area/project/other, 223 `ref/`, 1 daily |
| …of which carry a `^block-id` | 449 (53%) |

What the numbers say:

- **Usage is small and almost entirely same-note.** The migration is cheap. The same-note skew matches the picker's
  current-note restriction.
- **844 open tasks** is a tiny pool for in-memory fuzzy search. No index, server, or Rust call is needed.
- **47% of open tasks have no block ID.** The picker has to make creating an ID nearly free.
- **The 21 `#^ref` embeds are a hidden side effect.** The hooks treat any sole embedded task child as a rank edge,
  so linking "Read X" into today currently promotes the reference note's reading task too.

### 1.4 This would be the third format change in fourteen weeks

| Date | Commit | Representation |
| --- | --- | --- |
| 2026-06-28 | `f2cf0ab`, `b57a0bc` | One `**DEPENDS ON:** [[#^a]]` child bullet per dependency, beside `[dependsOn::]` |
| 2026-06-28 | `d33c4a6` | **One** managed `🔗 **DEPENDS ON:** [[#^a]] • [[#^b]]` line (same-note links only) |
| 2026-07-11 | `982ac8b`, plan `plan:202607/transcluded_task_deps.md` | One transcluded `![[#^id]]` bullet per dependency; `!` becomes the dependency gesture |
| 2026-07-11 → 16 | `fc90f46`, `9ec1b08`, `36296ec` | Path-qualified ids, target promotion, derived Blocked |

**The request is close to a return to the June design.**

- The July plan records *what* changed ("Bryan wants to replace that rendering") but not *why*.
- My inference: the June line showed only `^id` slugs (same-note only, with no live status), while an embed shows
  the dependency's checkbox and text and lets you tick it in place.

**The new design must keep those benefits, or the format will swing back again.** It needs:

- the live status and description of each dependency (the chip renderer, [§6.5](#65-rendering-dep-chips));
- a way to act on a dependency without leaving the page (Ctrl+Enter on a chip; [§6.6](#66-other-gestures)).

---

## 2. Is this a good idea?

### 2.1 Yes, for five concrete reasons

1. **Embeds render the target's entire subtree, nested.** Since Obsidian 0.13.25, embedding a list item also renders
   its children. In `body.md`:
   - `- ![[#^hospital-swarm]]` under the Rahway task renders that task plus its note and its six-line Schedule Log:
     **8 lines**.
   - `- ![[body#^rahway]]` under "Make appt for this…" renders the Rahway task, the nested hospital-swarm embed (8
     lines), its phone number, and its own Schedule Log.
   - So **one dependency costs about 12 rendered lines**. A Depends-On line costs one.
   - Users also report nested embeds stop rendering at about 5 levels.
2. **Embeds mix up "sub-task" and "prerequisite", and that has a dangerous side effect.**
   - The glossary defines transcluded child task links as "sub-tasks (i.e. dependencies)".
   - Two closers follow every embed in a task's block, recursively (depth 25, 250 targets): `bob capture =x` on an
     embedded ledger link (`linked_tasks.rs`) and task-status-cycler's Pomodoro tree close (`9941`).
   - So **closing a dependent can force-close its prerequisites.**
   - Example: `cash.md`'s "Set up Actual Budget" depends on "Save Verizon Router password", which depends on
     "unemployment". Closing an embedded `![[cash#^budget]]` ledger link would walk that chain.
   - Prerequisites should never be auto-completed because the thing that waited on them was closed.
3. **Dep embeds can't be told apart from other embeds.**
   - A dependency embed has the same text shape as a Pomodoro Task Link and a `#^ref` content embed.
   - The cost is special cases spread across three plugins and the hooks: the "id ∈ dependsOn" managed rule,
     block-id-prompt refusals, link-mode hiding the `dependsOn` row, and protecting `#^ref` embeds.
   - The hooks still get it wrong: the 21 `#^ref` embeds count as rank edges.
   - A labelled line ends the ambiguity at the syntax level.
4. **One bullet per dependency costs N rows.** A single line costs one row and wraps gracefully.
5. **`!` ties a rendering toggle to a data change.** "Show this inline" and "make this a prerequisite" are different
   intents. Splitting them makes both gestures predictable.

### 2.2 What the request leaves out

- **Which representation is the authority** (§1.2). Without one authority, one transaction, and one reconciler, the
  drift bugs carry over unchanged.
- **The picker.** Ctrl+Shift+P "already has support" only for the current note.
- **Rendering.** A raw `[[note#^id]]` shows as `note > ^id` in Live Preview. That is fine as a fallback but not
  beautiful.
- **The semantic change.** Closing a dependent will no longer close its prerequisites, and `#^ref` embeds will no
  longer promote reading tasks. Both are improvements, but they are behaviour changes and should be decided on
  purpose.
- **Rollout.** The MacBook runs `task-status-hooks` every 15 minutes. bob, the plugins, and the vault migration have
  to move in order (§7.3).

---

## 3. Options considered

### 3.1 Data model: which representation is authoritative?

| Option | Description | Verdict |
| --- | --- | --- |
| **A. Links only** | Drop `[dependsOn::]` / `[id::]`; Blocked and rank come from the line | **Rejected for now.** The Blocked plan (`plan:202607/blocked_task_status.md`) requires `dash.md` and `blocked.md` to stay on Tasks' `is not blocked` / `is blocked` and "must not be replaced with a fragile `status.name` or `status.symbol` filter". ledger-tools lane math (`planTaskIsBlocked` → `task.isBlocked`), the Rust lane queries, and Tasks parity all depend on the fields. Removing them is a cross-repo rewrite with no user-visible gain. |
| **B. Fields only, line drawn virtually** | Keep `[dependsOn::]`; draw chips from it; store no links | Rejected. It ignores the explicit request for normal links. It loses backlinks, Obsidian's rename link-update, plain-text, terminal, and git readability, and `bob capture` / Bob Mac Capture previews. |
| **C. Fields authoritative, line generated** | The line is a read-only projection of `[dependsOn::]` | Rejected. Hand-editing the visible line would be silently undone, so what you see is not what is true. |
| **D. Line authoritative, fields derived** ✅ | The Depends-On line is the truth; `[dependsOn::]` and `[id::]` are its projection, maintained by writers and repaired by the hooks | **Recommended.** It matches your CSS comment and the request ("use normal task links"). Hand edits work, and Tasks semantics stay intact. `[id::]` still travels with a task when it is cut and pasted, so the reconciler can heal broken links (§6.2). |

**ADJUSTMENT A1:** keep `[dependsOn::]` / `[id::]`, but demote them to a derived projection of the dep links.

### 3.2 Where the links live

| Option | Verdict |
| --- | --- |
| On the task line itself (`- [ ] #task Foo ⛓ [[#^a]] ^foo`) | Rejected. The links become part of the Tasks description and leak into queries, the dash, capture previews, picker titles, and fuzzy search. |
| One plain-link bullet per dependency | Rejected. Same N-row cost, and still looks like a Pomodoro Task Link. |
| Unlabelled single line (`- ⛓️ [[#^a]] · [[#^b]]`) | Possible. Shorter, but unclear in plain text, terminal, and diffs, and it breaks the "emoji + bold label" convention of the managed logs. Listed as open question Q2. |
| **Labelled single first-child line** ✅ | `⛓️ **DEPENDS ON:** [[#^a]] · [[note#^b]]`. Matches `🗓️ **SCHEDULE LOG**`, `🛠️ **WORK LOG**`, `❌ **CANCEL LOG**`, and your own `**PHONE NUMBER:** …` style. |

### 3.3 Editing UX

| Option | Verdict |
| --- | --- |
| Tasks' "Create or edit Task" modal ("Before this / After this") | Rejected as primary; it is good prior art. It searches the vault (same file first, at most 20 matches), but writes only ids, generates random 6-character ids that the cycler then has to normalise, has an open multi-dependency bug (#3252), and knows nothing about Blocked, lanes, or the line. |
| Keep `!` as the dependency gesture | Rejected. It is the rendering-vs-data coupling from §2.1. |
| **A vault-wide dependency stage inside Ctrl+Shift+P, plus chip affordances** ✅ | Keeps your muscle memory, reuses the Tab-mark batch convention, and supports counted `N<Ctrl+Shift+P>` and Task Link sessions. |

---

## 4. Requirement adjustments (all called out)

| # | Your requirement | Adjustment | Why |
| --- | --- | --- | --- |
| **A1** | "Use normal task links" | Links are the **authority**. `[dependsOn::]` / `[id::]` remain as a derived projection. | Tasks `is blocked` semantics are a recorded decision, and the fields cost nothing visually because your CSS already hides them. |
| **A2** | "All dep links on a single line, visually appealing" | A **managed** first-child line with a fixed grammar (`⛓️ **DEPENDS ON:**`, ` · ` separators), not a free-form line of links | Reliable parsing in Rust and two JavaScript plugins, and consistent with the managed-log family. |
| **A3** | "Beautiful" | No stored aliases and no stored strikethrough. Description and status are **drawn live** as chips. | Stored aliases go stale on rename, and a stored strike is derived state that can drift. |
| **A4** | (implicit) | `!` loses its dependency side effects and goes back to being a pure transclusion toggle. On a Depends-On line it is refused with a hint. | One gesture per intent. |
| **A5** | "Treated as dependencies" | Dep links are **prerequisites only** (finish-to-start). Closing a dependent never closes them, and `#^ref` embeds stop being rank edges. | Removes the recursive force-close hazard and the hidden rank edges. |
| **A6** | "Tasks in any area/project note" | The candidate pool is every open `#task` the hooks scan, excluding daily notes, `done/`, `_templates`, `_generated`, and dot-directories. That includes `ref/` reading tasks, the inbox, and `#hide` tasks (shown with a muted "hidden" chip, so a project's `^prj` task can be a dependency). | "Read the reference first" and "after project X ships" are real prerequisites. |
| **A7** | (implicit) | **Removing** a dependency recovers the parent from `[?]` to Ready immediately when nothing else blocks it. Today removal is status-neutral. | Now that the dependency list sits on the parent itself, the old reason ("no authoritative snapshot") no longer holds. Waiting up to 15 minutes would make removal feel broken. |
| **A8** | "Use Ctrl+Shift+P" | Ctrl+Shift+P **on a Task Link** may edit the linked task's dependencies, and Ctrl+Shift+P **on a Depends-On line** opens its parent's dependency stage directly. | The vault-wide writer no longer depends on the active buffer, and the old ambiguity (dep embed = Task Link) is gone. |
| **A9** | "Add a glossary term" | Add `task-dep-link`, **amend** the `task-link` strand (its "transcluded … sub-tasks (i.e. dependencies)" sentence becomes false), and add a decision record. | The glossary and decisions must not contradict the new contract. |

---

## 5. What a task dep link is (proposed vocabulary)

- **Task dependency link** (aka **task dep link**): a plain Task Link on a Depends-On line. This is the glossary
  term you asked for; the draft text is in §6.7.
- **Depends-On line**: the single managed first-child line that holds a task's dep links. I recommend defining it
  *inside* the task-dep-link strand rather than as its own term, to keep the glossary small.
- **Dependent** (the task with the line) and **prerequisite** (a link target). I recommend these words in notices
  and docs. "Blocked by" is reserved for the derived `[?]` state, because the line stays true after every
  prerequisite is done, while "blocked" does not.

---

## 6. Recommended design

### 6.1 Grammar

```markdown
- [?] #task Make appt for this [[#^doctor]] 7d after! [fresh:: 2026-10-01] [dependsOn:: body__rahway, sase_bug_bash__e2e-sase-8v] ^appt
	- ⛓️ **DEPENDS ON:** [[#^rahway]] · [[sase_bug_bash#^e2e-sase-8v]]
	- other notes…
	- 🗓️ **SCHEDULE LOG**
		- …
```

This example is a real `body.md` task with one hypothetical cross-note prerequisite added, to show both link forms.

**Writers always emit exactly this form:**

- **Marker:** `⛓️` (U+26D3 U+FE0F), one space, `**DEPENDS ON:**`, one space.
- **Links:** one link per prerequisite, separated by ` · ` (U+00B7, already used in Schedule Log entries and the
  status badge row).
- **Link form:** the shortest unambiguous plain block link, following the hooks' resolver:
  - `[[#^id]]` for a same-note target;
  - `[[basename#^id]]` when the basename is unique;
  - otherwise `[[dir/note#^id]]`.
  - Never an alias or an embed.
- **Order:** existing links keep their order; new ones are appended. The `[dependsOn::]` order mirrors the line.
- **Position:** the first direct child of the dependent task. If a `❌ **CANCEL LOG**` exists it stays first and the
  Depends-On line goes second.
  - Indentation reuses the task's existing child indent, otherwise parent indent plus one tab (today's
    `getDependencyChildIndent` rule).
  - The line travels with its task through grouping moves, Ctrl+Shift+M, and `move-done-tasks`.

**Readers accept looser input** and writers canonicalise it:

- the emoji is optional and the VS16 selector is optional;
- any of ` · `, ` • `, `,`, or whitespace between links;
- `!`-embedded, struck, or aliased links, all treated as plain prerequisites;
- a Depends-On line that is any direct child, not just the first.
- A label with no links means "no prerequisites", and the reconciler deletes it.

**A Depends-On line is never** a Pomodoro Task Link, a dedicated Task Link bullet, a task section, or a managed log.

**The recognisers need updating.** These recognisers must reject the line:

- the hooks' sole-embed edge matcher;
- block-id-prompt's dedicated-link regex;
- nav's Task Link regex;
- bob-cli's `is_section_title` and managed-log parsers.

### 6.2 Source of truth and reconciliation

**The Depends-On line is the truth. `[dependsOn::]` / `[id::]` are its projection.** `bob task-status-hooks`
applies these rules vault-wide on every run, in the same guarded snapshot-and-retry write as its status edits, so
Blocked derivation in that run already sees the reconciled set.

| # | Situation for one dependent task | Resolution |
| --- | --- | --- |
| R1 | Depends-On line present | `[dependsOn::]` := canonical ids of the line's resolvable task links, in line order, deduplicated. Each prerequisite gains a canonical `[id::]` if it lacks one. The field is removed when no resolvable link remains. |
| R2 | No line, but `[dependsOn::]` present (Tasks modal, hand-typed field, legacy) | **Adopt:** write the line from ids that resolve to a task with a `^block-id`. Ids that don't resolve stay in the field, with a warning. |
| R3 | A link doesn't resolve, but the parent's field still names an id whose `[id::]` now lives in another note (cut and pasted) | **Heal:** rewrite the link to the task's new location, then apply R1. |
| R4 | A link doesn't resolve and can't be healed | Keep it verbatim. Warn `unresolved_dependency_link`. It does not block (Tasks semantics). The chip shows as broken. |
| R5 | A link resolves to a block that isn't a task | Keep it, warn, and leave it out of the projection. |
| R6 | A link points to the task itself | Leave it out of the projection (so it can't block forever) and warn. The picker never offers it. |
| R7 | Dependency cycle | Keep it with Tasks semantics (every member stays Blocked). Warn `dependency_cycle` with the path. The picker refuses to create one. |
| R8 | Legacy sole `![[…]]` child whose id is in the field (the old managed rule) | The migration converts it. Hooks keep reading it as a dep link for one release, so mixed fleets agree. |
| R9 | Line with a label but no links | Clear the field and delete the line. |

**Hand edits in Obsidian.** Navigation-hotkeys runs R1/R9 on the edited task block once the cursor leaves the
Depends-On line, with a short debounce so a half-typed `[[` never flips Blocked.

- Deleting the whole line in the editor clears the field. The editor can see that change happen; the headless
  reconciler can't.
- **The one documented surprise:** if you delete the whole line *outside* Obsidian (for example in vim on athena),
  R2 adopts the leftover field back. To remove every prerequisite, delete the links but keep the label (R9), or use
  Ctrl+D.
- I chose adoption over dropping on purpose: an unattended reconciler that runs every 15 minutes should only add
  information it can see declared somewhere, never infer that you meant to delete something. This follows the same
  "never guess" rule as the hooks' resolver.

**Why `[id::]` still earns its place:** ids travel with the task line when it is cut and pasted, which block links
do not (Obsidian never updates block links when a block moves between notes). That makes R3 possible.

### 6.3 Blocked, rank, and close semantics

- **Derived Blocked is unchanged.** A task is `[?]` while any prerequisite is open or its `scheduled` date is in the
  future, using Tasks semantics. The input is now the R1 projection. The `task-status-is-derived` decision still
  holds; only the input it describes changes.
- **Rank propagation gets a new edge source.** Pomodoro roots promote their prerequisites to Next or In Progress with
  the same strongest-rank, cycle-safe queue, and recent-activity recovery uses the same edges. Only the edge set
  changes: the reconciled dep links replace "sole transcluded child".
  - This keeps "linking A today pulls its prerequisites forward", which sticky lanes already list as an accepted cost.
- **Close recursion no longer follows dependencies (A5).**
  - `bob capture =x` and task-status-cycler's tree close keep following real `![[…]]` embeds, so sub-content still
    closes with its owner.
  - A Depends-On line contains no embeds after canonicalisation, so a prerequisite is never auto-closed by closing
    something that depended on it.
- **`#^ref` embeds** stay content embeds. They stop being rank edges (open question Q1).

### 6.4 The Ctrl+Shift+P dependency stage

**Entry points (all open the same stage):**

| Where the cursor is | Gesture | Result |
| --- | --- | --- |
| A `#task` line | Ctrl+Shift+P → type `dep` → ↵ (or the row is listed early because "set properties first" already applies) | Edits this task's prerequisites |
| A dedicated Task Link in the ledger | Ctrl+Shift+P → Depends on | Edits the **linked** task's prerequisites in its own note (A8) |
| The Depends-On line | Ctrl+Shift+P | Opens the parent's stage directly, with no property step (A8) |
| A task line, counted | `N<Ctrl+Shift+P>` → Depends on | Edits the current task plus the next N; shows the mixed `k/n` state (existing semantics) |
| A rendered chip | `＋` chip / `×` on a chip | Opens the stage / removes that prerequisite (§6.5) |

Optional: a palette command "Edit task dependencies" that opens the stage directly, so you can bind it to a chord.
Ctrl+Shift+B looked unused in `hotkeys.json`, but I didn't check Obsidian's defaults.

**The property row.** It replaces today's raw `body__rahway, …` pill with a summary: `⛓ 2 · 1 open`, or `⛓ none`.
Ctrl+D on the row removes the whole line and its projection. That fixes today's orphaned embeds.

**Stage layout:**

```text
╭─ ⛓ Depends on — Launch swarm to find hospital ─────────────────────────────────╮
│ rah▌                                                                           │
│ 1 prerequisite · 0 open · type to search 844 open tasks · Tab mark · ↵ toggle  │
├────────────────────────────────────────────────────────────────────────────────┤
│ CURRENT                                                                        │
│ ✓ [x] Find hospital list from insurance portal        body · ^insurance   ↵ −  │
│ RESULTS                                                                        │
│   [ ] Call Rahway radiology about results             body          ＋ id      │
│   [/] Rahway parking permit renewal                   cash · ^rahway-permit    │
│ ⟲ [?] Make appt w/ Rahway Hospital for CT scan    would create a cycle         │
│ BLOCKED                                                                        │
│   [?] Rahway billing dispute                          cash   🔒 Blocked · 1    │
╰────────────────────────────────────────────────────────────────────────────────╯
```

This mockup is illustrative. Only the two Rahway and Launch-swarm tasks are real vault tasks; the other rows are
invented. The Rahway task already depends on "Launch swarm", so adding it here would close a loop and the row is
disabled.

**Candidates.** All open `#task` lines from the A6 pool, taken from the Tasks plugin cache. ledger-tools already
reads it through `obsidian-tasks-plugin.getTasks()` and refreshes it on `cache-update`. There is no per-keystroke
vault I/O, and the fallback is a one-time metadata-cache scan when Tasks isn't warm.

**Ranking** mirrors bob-cli's capture `:` picker (`capture_link_tasks.rs::rank`), so Obsidian and Bob Mac Capture
order results the same way:

- every whitespace-separated term must match;
- each term scores its best tier across description, `note:blockid`, block id, note route, and section heading:
  field prefix 3, word prefix 2, substring 1, in-order subsequence 0;
- scores are summed;
- ties keep canonical order: same note first, then In Progress, Next, Ready, with Blocked grouped beneath (as
  block-id-prompt already does).

With an empty query, the stage shows **Current**, then same-note open tasks, then the In Progress and Next lanes. At
most about 60 rows are rendered; the rest are reachable by typing.

**Keys:**

| Key | Action |
| --- | --- |
| type | Vault-wide fuzzy search |
| ↑ / ↓, Ctrl-N / Ctrl-P | Move |
| ↵ | **Toggle** the highlighted row (add if absent, remove if present) and close. With marks, apply every mark. |
| Tab | Mark / unmark (`＋ add`, `− remove`, `＋ id`) and move down. Disabled in counted sessions, as today. |
| Esc | Cancel. Nothing is written. |

**Guards.**

- Disabled rows show their reason: self, cycle (`⟲`, with the path in a tooltip), an unencodable note path (a
  pre-existing id-scheme limit: no spaces or dots), and a target that changed since the stage opened.
- Done and Cancelled tasks appear only under **Current**, so you can still remove them.

**Block IDs.** Targets without `^id` show `＋ id`. On apply, today's block-ID stage opens, pre-filled with the
`suggestBlockIdFromTask` slug, so ↵ accepts it. A batch prompts one target at a time. Closing it midway writes
nothing (today's semantics).

**What one gesture writes, as one atomic operation:**

| Change | Line | Projection | Dependent status | Prerequisite status |
| --- | --- | --- | --- | --- |
| Add | Append the link, creating the line if needed | Add the id; set the target's `[id::]` and `^id` | `[?]` if the target is open | **Commitment transfer:** an open target rises to at least the dependent's lane when the dependent was `[*]` or `[/]` (today's `!` behaviour, now shared by the picker) |
| Remove | Remove the link; delete the line when empty | Remove the id; leave the target's `[id::]` in place | **A7:** `[?]` → `[ ]` now, if no open prerequisite and no future `scheduled` remain; the hooks may raise it later | unchanged |

- Same-note edits are one editor transaction, so one Ctrl+Z undoes the whole gesture.
- Cross-note target writes use preimage-checked `vault.process`, as `!` does today.
- The dependent's line is stamped `[fresh:: today]` through `api.freshness.stampLine`, as all Ctrl+Shift+P rows do.

**Notices** say what happened in task words:

- `⛓ Now waits on "Call Rahway radiology" · Blocked`
- `⛓ No longer waits on "Find hospital list" · Ready again`
- `⛓ 2 added · 1 removed · Blocked (1 open)`

### 6.5 Rendering: dep chips

Here is how the Live Preview line looks when the cursor is not on it. Colours come from your existing
`--task-status-*` tokens, and this uses the same example as §6.1, so the second chip's description is invented:

```text
[?] Make appt for this doctor 7d after!                    ✓ today  🔗
    ⛓ depends on  ( ? Make appt w/ Rahway Hospital for CT… )  ( ○ Run e2e on sase-8v ↗ sase_bug_bash )  ＋   waiting on 2
```

**Chip anatomy:**

- a miniature of the target's own checkbox, rendered as `<span class="task-list-item-checkbox" data-task="?">`, so
  `task-statuses.css` colours it with no new palette;
- the cleaned description (the same cleaning as `cleanTaskDisplayText`), truncated to about 44 characters;
- `↗ note` for a cross-note target;
- a tooltip with the full text, note path, status name, and `scheduled` date.

**Chip states:**

- **Open:** normal.
- **Done:** a green `✓`, dimmed, with strikethrough text. When more than three prerequisites are done, the done
  chips collapse to `✓×N`.
- **Cancelled:** muted `✕`.
- **Broken (R4):** red, dashed, reading `⚠ ^id not found`.
- **Trailing summary:** `waiting on N`, or a green `✓ all done` so you can see at a glance why the task is
  (un)blocked.

**Interaction:**

- Click opens the target (Mod-click for a new tab) through `workspace.openLinkText`.
- Hovering shows Obsidian's native page preview through `workspace.trigger("hover-link", …)`. ledger-tools already
  uses both calls for its badges (`main.js:7272–7291`).
- On hover a `×` appears that runs the remove transaction. The trailing `＋` opens the stage.
- Moving the cursor onto the line shows the raw Markdown, as Live Preview always does.

**Implementation** reuses the freshness-mark pipeline in **bob-ledger-tools**, which already owns read-time task
views, the Tasks cache memo, the CM6 setup, and the reading-view post-processor:

- **Live Preview:** a `Prec.highest` view plugin that scans visible ranges only and checks each line cheaply with
  `indexOf("DEPENDS ON")`. Each chip is a replace widget whose `eq()` is keyed on its model, so unchanged chips don't
  flicker. Atomic ranges make each chip delete as a unit. Source mode stays raw.
- **Reading view:** a markdown post-processor that decorates the `a.internal-link` anchors inside the Depends-On
  list item, wrapped in a `MarkdownRenderChild` that updates when the cache refreshes.
- **Data:** chips read only the in-memory Tasks memo, with no disk reads during render. Refreshes are debounced
  through the existing `freshnessMarksRefresh`-style effect.
- **Accessibility:** each chip has an `aria-label` such as "Depends on: Make appt w/ Rahway Hospital for CT scan,
  Blocked".
- **Cross-plugin calls:** the `×` and `＋` actions call a small new versioned navigation-hotkeys `api`
  (`{version: 1, openDependencyStage(ref), removeDependency(parentRef, targetRef)}`), following task-status-cycler's
  `api` convention. Plugins still never import each other's `main.js`.

**The task line itself.** Your CSS already collapses `[dependsOn::]` to a muted link glyph and hides `[id::]`. Keep
that. Optionally upgrade the glyph to a `⛓ 1/2` mini-badge later.

**Without the plugin**, the line still reads well: `⛓️ DEPENDS ON: ^rahway · sase_bug_bash > ^e2e-sase-8v`. Slug
block IDs, which block-id-prompt already suggests, carry the meaning in git diffs, terminals, and `bob capture`
`task_blocks` previews.

### 6.6 Other gestures

| Gesture | Today | Proposed |
| --- | --- | --- |
| `!` / `N!` (navigation-hotkeys) | Toggles the embed and adds or removes the dependency | Pure transclusion toggle everywhere. On a Depends-On line: refused, with a notice pointing to Ctrl+Shift+P (A4). |
| Ctrl+Enter on a link on the line (task-status-cycler) | Closes the target and strikes the link; reopening **restores `![[…]]`** (`4697`/`4759`) | Closes or reopens the target without striking anything on a Depends-On line (status is drawn live), and never re-embeds it. Dependent recovery works as it does today. |
| Retirement and restore when a target closes or reopens elsewhere | Strikes `![[…]]` under `#task` lines | Skips Depends-On lines. Without this, the reopen path would corrupt the line. |
| Alt+] / Alt+[ on the line | Cycles an embedded target | Optional: cycles the target under the cursor's link. |
| Ctrl+Shift+Enter on the line (block-id-prompt) | Refuses dependency embeds | Refuses Depends-On lines. Otherwise it would delete one link token and unlink that task from today's Pomodoros. |
| Ctrl+D on the Depends-on row | Deletes only the field (bug) | Deletes the line and the field, with A7 recovery. |
| Ctrl+Shift+M and `move-done-tasks` | Rewrite ids and links to moved tasks | Unchanged, plus: re-qualify same-note `[[#^x]]` links *inside* a moved block whose target stayed behind (§9). |
| `bob capture` / Bob Mac Capture | No dependency grammar | Unchanged for now. The line shows as an ordinary child in `task_blocks` previews. Any future dependency syntax lands in bob-cli first, per the thin-client decision. |

### 6.7 Drafts for memory (to be written through `/sase_memory_write` at implementation time)

**New glossary strand `glossary:task-dep-link`:**

> # Task Dependency Link
>
> aka task dep link
>
> A plain (never embedded) Task Link to an Obsidian `#task` that must be completed before the task it sits under is
> unblocked. A task's dep links all live on its single Depends-On line — its first direct child,
> `⛓️ **DEPENDS ON:** [[#^a]] · [[note#^b]]` — and that line is the source of truth: Bob derives the task's
> `[dependsOn::]` field and each target's `[id::]` from it, and `bob task-status-hooks` keeps the task Blocked `[?]`
> while any target is open. Add or remove them with the Ctrl+Shift+P **Depends on** stage, which fuzzy-searches every
> open task in the vault, or by editing the line. A dep link is a prerequisite, not a sub-task: closing the dependent
> never closes its targets, and dep links never count as Pomodoro Task Links.

**Amend `glossary:task-link`.** Replace "As another special case, transcluded task links that are the only contents
of a sub-bullet on another Obsidian task are treated as sub-tasks (i.e. dependencies) of that task" with "Task Links on
a task's Depends-On line are [[glossary:task-dep-link]]s."

**New decision `decisions:task-deps-are-one-links-line`**, titled "Task Dependencies Are Links On One Depends-On Line":

- **Applies to:** bob-cli, bob-plugins, vault.
- **Claim:** §6.1–6.3, one paragraph.
- **Why:** §2.1.
- **Rejected:** links-only, fields-only virtual, field-authoritative generated line, per-dependency bullets, links on
  the task line, the Tasks modal, `!` as the gesture.
- **Cost:** three parsers kept in sync by vectors; the projection exists; whole-line deletion outside Obsidian is
  re-adopted; `#^ref` embeds lose rank propagation.
- **Reopens when:** the projection drifts in practice (R1/R2 warnings > 0 on most hooks runs for two weeks), or Tasks
  `is blocked` stops being load-bearing.
- **Effect on existing records:** it updates the "transcluded dependency path" wording of `task-status-is-derived`.
  That record's Blocked rule stands.

---

## 7. Implementation plan

### 7.1 Phases

| Phase | Repo | Work | Size |
| --- | --- | --- | --- |
| P0 Contract | bob-cli + memory | `docs/task-dependencies.md` (grammar, R1–R9, gestures). Shared conformance vectors for parsing, canonical writing, and R1–R9 outcomes, using the Today / walk-vector pattern. Glossary strand, `task-link` amendment, decision record. | S |
| P1 Hooks | bob-cli | A new `task_dependencies` module with a parser (reusing `pomodoro.rs::block_link_occurrences`) and a writer (reusing freshness field placement). Hooks reconcile R1–R9 before Blocked derivation. Rank edges come from the reconciled set; legacy sole embeds are still read (R8). Additive JSON: `dependency_lines`, `dependency_projection_updates`, `adopted_dependency_lines`, `healed_dependency_links`, `dependency_warnings`. Human output sections, docs, `--help`. Make `is_section_title` and the managed-log parser ignore the line. | M |
| P2 Picker and writers | bob-plugins: navigation-hotkeys | The vault-wide dependency stage (§6.4), one dependency transaction (add / remove / commitment transfer / A7 recovery), Depends-On-line and Task Link entry points, the Ctrl+D fix, the hand-edit mirror, `!` decoupling, and the `api` v1. Delete the legacy DEPENDS ON / consolidate code once migration is done. | L |
| P3 Compatibility | task-status-cycler, block-id-prompt | Skip strike and restore on Depends-On lines. Tree close ignores the line. Ctrl+Enter on a dep link never re-embeds. Ctrl+Shift+Enter refuses the line. Additive cycler `api.recoverBlockedTasks(parents)` for A7. Teach the id normaliser about the line (it currently only touches fields). | M |
| P4 Chips | bob-plugins: ledger-tools | Live Preview and Reading view chips (§6.5), CSS on `--task-status-*` tokens, render vectors. | M |
| P5 Migration | bob-plugins script + vault | `scripts/migrate-dependency-lines.mjs`, dry-run first (details in §7.2). | S |

Everything lands in bob-cli and bob-plugins. The vault changes only through the migration and later reconciler runs.

### 7.2 Migration

- **Convert:**
  - 38 live dependency embeds and 5 struck retired links into Depends-On lines on 43 parents;
  - 2 field-only closed parents through R2.
- **Leave as they are:**
  - the 21 `#^ref` embeds, which are not dependencies;
  - Pomodoro ledger embeds in daily notes.
- **Preserve:** the existing tab / 2-space indentation of each block.
- **Expected run:** about 18 notes changed. A second run must be a no-op.
- **Before the write:** cross-check with a `bob task-status-hooks --dry-run --format json` diff (there should be no
  Blocked flips).
- **Commit:** in the vault through `/sase_git_commit`, per the vault's `AGENTS.md`.

### 7.3 Rollout order (several machines)

athena, apollo, and the MacBook each have their own `bob` binary and their own plugin deployment, and the MacBook
runs the hooks every 15 minutes. So:

1. Ship P1 everywhere, reading **both** formats.
2. Ship P2–P4 everywhere with `bob plugins sync`.
3. Run P5.
4. Remove legacy embed reading after one release.

Running the migration before step 1 finishes on the MacBook would make its old hooks drop the rank edges, though not
Blocked, which comes from the fields.

### 7.4 Testing

- **Shared vectors:** consumed by Rust unit tests and `node --test` suites in navigation-hotkeys, ledger-tools,
  task-status-cycler, and block-id-prompt.
- **Hooks integration fixtures:**
  - same-note, cross-note, and basename-ambiguous links;
  - R2 adoption, R3 heal, R4/R5 warnings, R7 cycle;
  - a legacy embed read during the transition;
  - no rank edge for `#^ref` embeds;
  - idempotency.
- **Plugin tests:**
  - one undo step per gesture;
  - cross-note preimage failure leaves nothing behind;
  - the counted mixed-state stage;
  - cycle-guard rows;
  - Ctrl+D removes line and field;
  - `!` refused on the line;
  - reopening a target never re-embeds.
- **Manual pass in Obsidian:** chips in Live Preview and Reading view, hover preview, and a line that wraps on mobile
  width.

---

## 8. Risks and open questions

| Risk | Mitigation |
| --- | --- |
| Three parsers (Rust, nav, ledger-tools) plus two recognisers drift apart | One grammar doc and shared vectors. Recognisers are a single regex copy. |
| The projection is still a second representation | One authority (the line), writers that update both together, and an idempotent vault-wide reconciler with reported counts. The decision record's reopen trigger watches drift. |
| The hooks now write fields in other notes (target `[id::]`) | Same guarded pipeline (snapshot, byte re-check, quiet period, recovery copies). Dry-run shows every write. |
| Hand edits flicker Blocked while typing | The mirror runs when the cursor leaves the line, not on every keystroke. |
| Format churn (a third change) | Keep what made embeds attractive: live status (chips) and acting in place (Ctrl+Enter on a chip). |

**Questions for Bryan:**

- **Q1.** Should `#^ref` reading-task embeds keep promoting their reading task when the parent is linked today? I
  recommend no: they are content. If you want that behaviour, make the reading task a real dep link.
- **Q2.** Do you want the label (`⛓️ **DEPENDS ON:**`), or just the emoji (`⛓️ [[…]] · […]`)? And `⛓️` or the
  legacy `🔗`? I recommend the label with `⛓️`: it gives the new format an unambiguous signature during the
  mixed-fleet rollout and won't trip old `🔗` code paths.
- **Q3.** Should commitment transfer (an added prerequisite inheriting the dependent's Next / In Progress lane) apply
  to picker adds? I recommend yes, to match `!` today. The alternative is that a blocked Pending task's commitment
  quietly vanishes.
- **Q4.** Should a reverse "Blocks…" row (pick tasks that should wait on *this* one, like Tasks' "After this") ship
  in P2 or later? I recommend later: it writes other tasks' lines and is less common.

---

## 9. Problems found along the way (independent of this redesign)

1. **task-status-cycler: Alt+] / Alt+[ to Done or Cancelled skips `finalizeClosedTasks`** (`handleCycleCommand`
   8226 → `setActiveCheckboxStatus`; verified). Cycling a prerequisite closed recovers its Blocked dependents only on
   the next hooks run, while Ctrl+Enter recovers them immediately. Filed as task bead `bob-cli-3k`.
2. **navigation-hotkeys: Ctrl+D on `dependsOn` orphans embeds and leaves `[?]`** (31490–31588). P2 fixes it.
3. **navigation-hotkeys: "Rewrite dependency navigation links (current note)" can delete cross-note embeds**
   (26045–26066). P2 deletes the command. Until then, avoid running it on notes with cross-note dependencies.
4. **navigation-hotkeys: picker badge `↵ ^<value>` shows the path-encoded id** (for example
   `^projects__Here__x`), not the block id. Cosmetic, and replaced in P2.
5. **`move-done-tasks`: same-note `[[#^x]]` links inside an archived block can dangle** when `^x` stays behind.
   `repair_wiki_link_inner` rewrites only links whose *target* moved (`collect_done/link_repair.rs:651`). It affects
   archive history only, but P1/P5 should qualify such links.

---

## 10. Recommended solution

**Replace transcluded dependency sub-bullets with task dep links on one managed Depends-On line, make that line the
source of truth, and edit it from a vault-wide Ctrl+Shift+P stage. Chips draw it beautifully.**

1. **Format (A2).**
   - Each dependent task gets one first-child line: `- ⛓️ **DEPENDS ON:** [[#^a]] · [[note#^b]]`.
   - Shortest plain block links, ` · ` separators, no aliases, no strikethrough, no embeds.
   - A label with no links means none.
2. **Authority (A1).**
   - The line is the truth. `[dependsOn::]` and `[id::]` remain as its derived projection, for Tasks `is blocked`
     semantics.
   - Every writer updates line and projection in one transaction.
   - `bob task-status-hooks` reconciles vault-wide (R1–R9): it projects, adopts field-only dependencies, heals moved
     targets through `[id::]`, and warns on broken links and cycles.
3. **Semantics (A5).**
   - Blocked stays derived, now from the projection.
   - Rank propagation follows dep links.
   - Dependencies are prerequisites, never sub-tasks: closing a dependent never closes them, and `#^ref` embeds stop
     being edges.
4. **Editing (A6–A8).**
   - Ctrl+Shift+P → **Depends on** opens a stage that fuzzy-searches every open vault task, ranked like bob's capture
     `:` picker.
   - ↵ toggles one dependency; Tab marks several. Cycles are refused, and block IDs are created in place.
   - Adding blocks the dependent and transfers its lane to the prerequisite. Removing recovers it to Ready
     immediately when nothing else blocks it.
   - The same stage opens from a Task Link, from the Depends-On line itself, counted, and from the chips' `＋` / `×`.
   - Ctrl+D removes everything cleanly.
   - `!` goes back to being only a transclusion toggle (A4).
5. **Beauty (A3).**
   - ledger-tools draws each dep link as a status chip in Live Preview and Reading view: the target's real checkbox
     glyph and colour, its live description, a `↗ note` suffix, native click and hover preview, `×` to remove, `＋`
     to add, and a `waiting on N` / `✓ all done` summary.
   - Without the plugin, the raw line is still readable.
6. **Vocabulary (A9).**
   - Add `glossary:task-dep-link` (draft in §6.7) and amend `glossary:task-link`.
   - Record the decision "Task Dependencies Are Links On One Depends-On Line".
7. **Delivery.**
   - P0 contract and vectors → P1 bob-cli hooks (reading both formats) → P2 navigation-hotkeys stage and writers →
     P3 cycler and block-id-prompt compatibility → P4 ledger-tools chips → P5 a dry-run-first migration of 44 tasks in
     about 18 notes.
   - Deploy bob and the plugins on every machine before migrating. Remove legacy embed reading one release later.
