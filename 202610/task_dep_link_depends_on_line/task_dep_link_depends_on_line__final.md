# Task Dependency Links: One Depends-On Line, a Vault-Wide Picker, and Live Chips

- **Lead researcher:** consolidated report (Fri 2026-10-02). It merges five independent reports (`__cdx`, `__cld`,
  `__grk`, `__mus`, `__gem` in this directory) and adds my own verification. That verification targeted the points
  where they disagreed or gave weak evidence.
- **Snapshot:** bob-cli `8f01f33`; bob-plugins `ede89d3` (navigation-hotkeys 1.50.0, task-status-cycler 1.19.0,
  block-id-prompt 1.17.0, ledger-tools 1.17.0); vault checkout `gh:bobs-org/bob` at `8d80e01a`; audited memory
  `glossary:task-link`, `decisions:task-status-is-derived`, `decisions:task-lanes-are-sticky`.
- **Scope:** research only. No code, vault note, config, or memory file was changed.

## Bottom line

**Build it.** Dropping transclusions in favour of plain links on one line is the right direction. But the line
format is the smallest part of the job. Five reports and my own checks agree that the current pain comes from three
other places:

1. **The picker can't see the vault.** Today the Ctrl+Shift+P `dependsOn` stage only lists open tasks **in the
   current file** (verified: it reads `this.getEditorContent()`, and its empty state is "No open tasks in this file").
   That is why 44 of the vault's 45 dependency edges are same-note.
2. **Two different graphs answer two different questions.**
   - "Is this task Blocked?" is read from `[dependsOn::]`.
   - "What gets promoted, or closed, along with this task?" is read from transcluded child bullets.
   - They only agree as long as every writer keeps them in sync, and several writers don't.
3. **Embeds mix up "prerequisite" with "sub-content".** Closing an embedded ledger link can recursively close the
   prerequisites it transcludes. Reading-material `#^ref` embeds also quietly act as promotion edges.

My recommendation:

- Put a task's prerequisites on **one managed first-child line**: `⛓️ **DEPENDS ON:** [[#^a]] • [[note#^b]]`.
- Make that **line the source of truth**. Keep `[dependsOn::]` / `[id::]` as a derived index for Obsidian Tasks.
- Edit the line from a **vault-wide Ctrl+Shift+P → Depends on stage**.
- Render each link as a **live status chip**. Without chips, the format will probably swing back to embeds a third
  time.

I make ten requirement adjustments, called out as **ADJ-1…ADJ-10** in §4. The full recommendation is in §9.

---

## 1. How dependencies work today (verified)

| # | Fact | Evidence |
| --- | --- | --- |
| F1 | **Blocked `[?]` comes from fields.** `task_dependency_states()` resolves `[dependsOn::]` ids against vault-wide `[id::]`. | bob-cli `task_status_hooks/sync.rs:678` |
| F2 | **Promotion comes from embeds.** `dependency_edges()` turns *any* sole transcluded block link in a direct child into a rank edge. It never checks that the target is in `dependsOn`. | `task_status_hooks/references.rs:307–383` (read this session) |
| F3 | **Closing an embed walks the whole tree.** `bob capture =x` on an embedded ledger link follows every embedded token in the closed task's block, recursively (25 levels, 250 targets). Task-status-cycler's Pomodoro tree close does the same. | `capture_pomodoro_close/linked_tasks.rs:540–620`, `embedded_children()` at `:1189` (read this session); cycler `main.js:9941` |
| F4 | **The picker is current-file only.** `showLocalTaskValueStage()` builds candidates from `getEditorContent()` and filters them with unscored `fuzzyMatchesText`. Results stay in document order. | navigation-hotkeys `main.js:22240–22282` (read this session) |
| F5 | **The compact row is legacy.** The `🔗 **DEPENDS ON:** [[#^a]] • [[#^b]]` row is recognized only so it can be migrated *away*. New writes emit one `![[…]]` bullet per dependency and store `~~[[…]]~~` for closed targets. The link regex only matches same-note `[[#^id]]`. | `main.js:241–267`, `formatDependencyNavigationBulletWithMarker` at `:1433` (read this session) |
| F6 | **Ctrl+Shift+P is a user binding.** `bob-navigation-hotkeys:set-bullet-property` is bound to Ctrl+Shift+P in the vault's `hotkeys.json`; the plugin declares no default. This settles mus's open question. | vault `.obsidian/hotkeys.json` (read this session) |
| F7 | **The picker's existing keys:** ↑/↓ and ^N/^P move, ⇥ marks, ↵ either links one task or applies the marks, Esc dismisses. | `BULLET_PROPERTY_LOCAL_TASK_HINTS`, `getBulletPropertyLocalTaskHints` |
| F8 | **Bryan's CSS already treats the fields as derived from the links:** "`[id::]` and `[dependsOn::]` are both derived deterministically (block id and transcluded block links), so their pills are noise". `[id::]` is hidden; `[dependsOn::]` shrinks to a muted glyph. | vault `.obsidian/snippets/dataview-properties.css:134–136` (read this session) |
| F9 | **The vault already has a compact link row**, for sub-projects: `🧩 **Sub-projects:** [[a]] • [[b]] • ~~[[c]]~~ ✅`. | `bob.md:12`, `sase_art.md:12` |
| F10 | **Other dependency gestures have gaps:** <ul><li>Task Link mode hides the `dependsOn` row.</li><li>Ctrl+D on `dependsOn` deletes only the field, orphaning the embeds and leaving the parent `[?]`.</li><li>"Rewrite dependency navigation links (current note)" can delete cross-note embeds.</li><li>Picker writes take several undo steps.</li></ul> | cld §1.2 (`main.js:15382`, `31490–31588`, `26045–26066`) |
| F11 | **Embed widgets have already cost editor-stability fixes.** gem's commits are real: `5337f45` (2026-07-15, "preserve viewport on transclusion toggle") and `30ae7b9` (2026-08-21, "preserve vim navigation after transclusion toggle"). | bob-plugins `git log` (read this session) |
| F12 | **The hooks' quiet interval is narrow.** The two-second quiet interval only guards notes that need *structural status grouping*, not every write. | `docs/task-status-hooks.md:660–664` (read this session) |
| F13 | **Excluded directories differ by tool.** The hooks skip `.git`, `.obsidian`, `_conflicts`, `_generated`, `done/`, and dot-dirs. The Tasks global query and ledger-tools also exclude `_conflicts`. | `src/native.rs:3`, `task_status_hooks/parse.rs:38`; ledger-tools `main.js:3012,3093` |
| F14 | **Removal is status-neutral today, on purpose.** The `!` keymap blocks on add but not on remove, "because only a whole-vault scan knows every remaining dependency". Keymaps may apply the rules early "for feedback"; the hooks have the final word. | `decisions:task-status-is-derived` |

### Vault census (2026-10-02)

| Measure | Count | Source |
| --- | ---: | --- |
| Tasks with a non-empty `[dependsOn::]` | 44 (14 open, all `[?]`; 24 done; 6 cancelled) | cld, grk (`bob query`) |
| Dependency edges, same-note / cross-note | 44 / **1** | cld; my scan of active notes agrees (1 cross-note) |
| Open tasks currently `is blocked` | 13, all from dependencies, none from schedules | grk |
| Dependency child bullets | 38 live embeds + 5 struck `~~[[…]]~~` | cld |
| Sole embeds under a `#task` that has **no** `dependsOn` | 21, all `#^ref` reading embeds; each one is a rank edge today | cld; mechanism verified in F2 |
| Open tasks in the picker pool | 844 in 278 notes; 449 (53%) have a `^block-id` | cld |
| Open-task lines in `_conflicts/` sync copies | **287** (duplicates of `sase.md` and `bob.md`) | my scan |
| Notes with open tasks whose path the current id encoder can't represent (space, dot) | **0** outside `_conflicts/` | my scan |

Most tasks have one dependency (maximum two). A few prerequisites fan out to several dependents (`cash__unemployment`,
`job__update-goog-end-date`). The migration is small: about 18 notes.

### The format has already changed twice

| Date | Commit | Representation |
| --- | --- | --- |
| 2026-06-28 | `f2cf0ab`, `b57a0bc` | One `**DEPENDS ON:** [[#^a]]` child bullet per dependency |
| 2026-06-28 | `d33c4a6` | **One** `🔗 **DEPENDS ON:** [[#^a]] • [[#^b]]` row (same-note only) |
| 2026-07-11 | `982ac8b` (`plan:202607/transcluded_task_deps.md`) | One `![[#^id]]` bullet per dependency; `!` becomes the dependency gesture |

**This request is close to a return to the June row.** The July plan records *what* it changed, not *why*. The likely
reason is that the June row showed bare `^id` slugs with no status, while an embed shows the prerequisite's checkbox
and text. The new design has to keep that benefit, or the format will swing back again. That is why §6.5's chips are
part of the requirement, not polish.

---

## 2. Is this a good idea? Critique

**Yes.** The evidence:

1. **Embeds render whole subtrees.** In `body.md`, the Rahway task's single `![[#^hospital-swarm]]` renders that
   task, its note, and its six-line Schedule Log. Nested embeds compound this: about 12 rendered lines per dependency,
   compared with one line for the row.
2. **One line can't hold embeds.** Obsidian block embeds render as blocks, so `![[a]] ![[b]]` on one source line still
   stacks two full task trees. The "single line" requirement already rules out transclusion.
3. **Embeds make prerequisites act like sub-content.** F3 means closing a dependent through an embedded ledger link
   can force-close the prerequisites it transcludes. Prerequisites should never be closed just because something that
   waited on them was closed.
4. **Embeds look identical to other embeds.** A dependency embed has the same text shape as a Pomodoro Task Link or a
   `#^ref` content embed. The cost is special cases in three plugins plus the hooks, and the hooks still get it wrong
   (F2: 21 hidden rank edges). A labelled line removes the ambiguity in the syntax itself.
5. **`!` ties a display toggle to a data change.** "Show this inline" and "make this a prerequisite" are different
   intents.
6. **Embed widgets have already needed viewport and Vim fixes** (F11).

**What the request leaves out** (each item is handled below):

- **Which copy is authoritative.** Without one authority, one transaction per gesture, and one reconciler, today's
  drift bugs (F10) carry over to the new format unchanged.
- **The picker scope** (F4). "Already supports dependencies" is only true for the current note.
- **Rendering.** A bare `[[sase_bug_bash#^e2e-sase-8v]]` shows in Live Preview as `sase_bug_bash > ^e2e-sase-8v`.
  That works as a fallback but isn't beautiful.
- **Semantic changes.** Closing a dependent will stop closing its prerequisites, and `#^ref` embeds will stop
  promoting reading tasks. Both are improvements, but they are behaviour changes and should be chosen on purpose.
- **Rollout order.** athena, apollo, and the MacBook each run their own `bob` binary, and the MacBook runs the hooks
  every 15 minutes. If the vault is migrated before every machine's hooks can read the new line, promotion edges
  silently disappear.

**Usage guidance worth writing down** (from cdx): a dep link means a *hard prerequisite*, combined with AND logic
(the dependent waits for every listed prerequisite, finish-to-start). It does not mean "related", "nice to do first",
or project hierarchy; prose links cover those. Overusing hard dependencies produces a backlog that looks Blocked even
when useful work is possible. Don't add OR-groups, lags, or a graph canvas in this change.

---

## 3. Where the researchers disagreed, and how I resolved it

| Question | Positions | Resolution |
| --- | --- | --- |
| **Which copy is the source of truth?** | cdx, grk, mus, gem: the `[dependsOn::]` field, with the row as a projection. cld: the row, with the fields derived from it. | **The row** (cld), plus cdx's safety rules (§6.2). Bryan's own CSS says the fields are "derived deterministically (block id and … block links)" (F8). The July field-hiding plan called the field a duplicate of the links. The request itself says to use links "for this". So the row is the authority Bryan already has in mind, and the field is hidden while the row is what everyone sees and edits, including Bryan in vim and agents. Obsidian updates links when a note is renamed; it doesn't update ids. The field stays as the Tasks index and as a breadcrumb for healing moved targets (`[id::]` travels with a cut-and-pasted task; block links don't). The cost is that dependency edits made in the Tasks plugin's modal to a task that already has a row get dropped, with a warning. That is the trigger for reopening this (Q5). |
| **Write aliases (`[[x#^id\|Title]]`)?** | cdx, grk, gem: yes. cld: no, draw titles live. | **Writers don't emit aliases; readers accept them.** Chips show the live title. Stored aliases go stale and double the length of the raw line. Slugged block IDs (`^hospital-swarm`) stay readable in plain text. This is the one easily reversible choice: if chips slip, writers can start adding aliases without changing the grammar. |
| **Store `~~strike~~` for closed prerequisites?** | gem: yes (today's writer does). cdx, cld, grk: no, show it live. | **No.** A stored strike is derived state that every closer (Ctrl+Enter, Alt+], `=x`, Mac Capture, hand edits, agents) would have to keep in sync across the vault. That is the same drift problem this redesign is removing. Chips show done state immediately, and existing struck links are normalized during migration. |
| **Separator and emoji** | Separator: ` • ` (grk, gem, mus; also the legacy row and Sub-projects) vs ` · ` (cld, cdx). Emoji: 🔗 (cdx, grk, gem, mus) vs ⛓️ (cld). | **` • ` and ⛓️.** ` • ` matches the vault's existing link row (F9). ⛓️ means "dependency chain", where 🔗 just means "link". It also keeps machines that haven't been updated safe. Old navigation-hotkeys code still matches `🔗 **DEPENDS ON:** [[#^a]]` (F5) and would rewrite such a row back into embeds on its next picker or consolidate run. Its regex can't match a ⛓️ row. Since 44 of 45 edges are same-note, this would affect almost every row. |
| **Search scope** | gem: area and project notes only, citing performance. Everyone else: all open tasks. | **All open tasks.** Order results by rank instead of excluding notes. At 844 tasks, in-memory filtering is trivial, so gem's performance concern doesn't apply. "Read this first" (`ref/`) and inbox tasks are real prerequisites. |
| **`#hide` tasks** | cdx: hidden by default behind a toggle. grk: skipped. cld: included with a muted chip. | **Include them, muted and ranked lower.** Depending on a project's `#hide` root task ("after project X ships") is a valid use, and no toggle is needed. |
| **Enter in the stage** | cdx: a staged editor (↵ toggles and stays open, Ctrl+↵ applies). grk: ↵ writes immediately and stays open. cld, gem: the existing convention. | **Keep the existing bob convention (F7):** ↵ toggles the highlighted task and closes; ⇥ marks several; ↵ with marks applies them all. This keeps muscle memory across every bob picker, writes one transaction per gesture, and still supports multi-select. |
| **`!`** | grk: `!` on a parent task opens the picker. cld: `!` goes back to being a pure transclusion toggle. cdx: keep a legacy adapter. | **cld.** `!` already toggles embeds on block links in the current line, including inline links on task lines, so overloading it on task lines would collide with that. Use one gesture per intent. |
| **Where promotion edges come from** | mus: the row plus legacy embeds, combined. cdx, grk: the field graph. cld: the reconciled row. | **The reconciled set** (row = field after projection). Legacy embeds count only if their id is already in `dependsOn`, and only for one release. `#^ref` embeds stop being edges. |
| **Removing a dependency** | Today: status-neutral (F14). cld: unblock immediately. cdx: let existing recovery logic decide once no blocker remains. | **Unblock immediately when nothing else blocks.** The decision record allows keymaps to apply the rules early "for feedback". Its reason for staying neutral (only a vault scan knows the remaining dependencies) no longer applies: the full list sits on the parent, and the Tasks cache knows each target's status. The hooks keep the final word. |
| **Path-to-id encoding** | cdx: a new v2 hex codec. cld: refuse paths it can't encode. | **Refuse visibly and defer the codec.** No active note is affected (census), and the `a/b.md` vs `a__b.md` collision is theoretical. Revisit when a note actually needs it. |
| **Ranking** | cld: port bob-cli's capture `:` ranker. cdx: Obsidian's `prepareFuzzySearch`. grk: the existing subsequence matcher. | **Port `capture_link_tasks.rs::rank`** (tier sum, then canonical order; verified at `:256`). Obsidian and Bob Mac Capture will then order results the same way, with shared test vectors. |
| **Chip host** | cld: ledger-tools. grk: navigation-hotkeys. | **ledger-tools.** It already owns read-time task views, the Tasks-cache memo, the CM6 decoration pipeline (freshness marks), and a Reading-view post-processor. |

**Claims I rejected after checking:**

- **mus:** "~80% built", "the canonical format already exists", "the link regex already supports `[[Note#^id]]`", and
  "the picker is vault-wide". All four are contradicted by F4 and F5: the row is legacy, writers emit embeds, the
  regex is same-note only, and the picker is current-file only.
- **gem:** "embedded checkboxes fail to invoke hooks" and "Dataview counts transcluded tasks twice". Neither is
  verified; I don't rely on them.
- **gem:** Schedule and Work Log labels use `🗓️ **SCHEDULE LOG**` and `🛠️ **WORK LOG**` (no colon, no ⏱️).

---

## 4. Requirement adjustments (called out)

| # | You asked | I recommend | Why |
| --- | --- | --- | --- |
| **ADJ-1** | "Use normal task links" | The links are the **authority**. `[dependsOn::]` / `[id::]` stay as a **derived index**, written in the same transaction and repaired by the hooks. | Tasks' `is blocked`, `dash.md`/`blocked.md`, ledger-tools lane maths, and Rust lane queries all read the fields. Removing them would mean a cross-repo rewrite with no visible gain. The CSS already hides them. |
| **ADJ-2** | "All dep links on a single line" | One **managed** first-child line with a fixed grammar that may **wrap visually**. | It needs reliable parsing in Rust and three JavaScript plugins. An unwrapped line is unreadable in narrow panes. |
| **ADJ-3** | "Visually appealing / beautiful" | **Live status chips** (Live Preview and Reading view). No stored aliases or strikes. **Don't migrate the vault until chips ship.** | Without live status, this is just the June row again, and the format will swing back to embeds. |
| **ADJ-4** | "Treat as dependencies" | Dep links are **prerequisites only**. Closing a dependent never closes them. `#^ref` embeds stop being promotion edges. | Removes the recursive force-close hazard (F3) and the 21 hidden rank edges (F2). |
| **ADJ-5** | (implicit) | `!` goes back to being a **pure transclusion toggle**. On a Depends-On line it is refused with a hint. | One gesture per intent. |
| **ADJ-6** | "Tasks in any area/project note" | Search **every open task** the Tasks global filter and the hooks agree on. Exclude daily notes, `done/`, `_templates`, `_generated`, `_conflicts`, and dot-dirs. Include `ref/`, inbox, Blocked, and `#hide` (muted). | Prerequisites live outside area and project notes too. `_conflicts/` alone would add 287 duplicate results. |
| **ADJ-7** | "Use Ctrl+Shift+P" | Ctrl+Shift+P is **the main door, not the only one.** The same stage also opens from the Depends-On line (no property step), from a Task Link (edits the linked task), from chip `＋`/`×`, and from a bindable "Edit task dependencies" command. | Fewer keystrokes for a frequent edit, and the stage is easy to discover from wherever the cursor is. |
| **ADJ-8** | (implicit) | **Removing** a dependency unblocks the parent immediately when nothing else blocks it. | Waiting up to 15 minutes would make removal feel broken (F14 allows early feedback). |
| **ADJ-9** | "Any note" | The current id encoder can't represent paths with spaces or dots. Show those targets as **disabled with a reason**, and defer a new codec. | No active note is affected today. Don't promise more than the encoder can handle. |
| **ADJ-10** | "Add a glossary term" | Add `task-dependency-link`, **amend** `task-link` (its "transcluded … sub-tasks (i.e. dependencies)" sentence becomes false), and add a decision record. | The glossary and the decision records must not contradict the new contract. |

---

## 5. Vocabulary

- **Task Dependency Link** (aka **task dep link**): a plain Task Link on a Depends-On line. It is the glossary term you
  asked for; the draft is in §6.7.
- **Depends-On line**: the single managed first-child line that holds a task's dep links. Define it inside the
  dep-link strand rather than as its own glossary term.
- **Dependent** (the task that has the line) and **prerequisite** (a link target): use these words in notices and
  docs. Keep "Blocked" for the derived `[?]` state. The line stays true after every prerequisite is done; "blocked"
  doesn't.

---

## 6. Recommended design

### 6.1 Grammar

```markdown
- [?] #task Make appt w/ Rahway Hospital for CT scan! [id:: body__rahway] [dependsOn:: body__hospital-swarm, sase_bug_bash__e2e-sase-8v] ^rahway
	- ⛓️ **DEPENDS ON:** [[#^hospital-swarm]] • [[sase_bug_bash#^e2e-sase-8v]]
	- **PHONE NUMBER:** (732) 381-4200
	- 🗓️ **SCHEDULE LOG**
		- …
```

This is the real `body.md` task with one cross-note prerequisite added (hypothetically) to show both link forms.

**Writers always produce exactly this form:**

- **Marker:** `⛓️` (U+26D3 U+FE0F), one space, `**DEPENDS ON:**`, one space.
- **Separator:** ` • ` between links.
- **Link form:** the shortest plain block link that is unambiguous under the hooks' resolver:
  - `[[#^id]]` for a target in the same note;
  - `[[basename#^id]]` when the basename is unique;
  - otherwise `[[dir/note#^id]]`.
  - Never an alias, an embed, or a strike.
- **Order:** existing links keep their order and new ones are appended. Removing a link and adding it again moves it
  to the end. The `[dependsOn::]` order mirrors the line. Don't re-sort when statuses change, so git diffs stay quiet.
- **Position:** the first direct child of the dependent. If a `❌ **CANCEL LOG**` exists, it stays first and the
  Depends-On line goes second.
  - Indentation reuses the task's existing child indent, otherwise parent indent plus one tab.
  - Keep the existing line endings and final newline.
  - The line moves with its task through Ctrl+Shift+M, grouping moves, and `move-done-tasks`.
- **Empty list:** the line is deleted and the field is removed. There is no "none" placeholder.

**Readers accept looser input, and writers canonicalise it:**

- the emoji may be missing, or be the legacy 🔗; the VS16 selector is optional;
- either label, `DEPENDS ON` or the legacy `DEPENDENCIES`;
- any of ` • `, ` · `, `,`, or whitespace between links;
- aliased, struck, or `!`-embedded links, all treated as plain prerequisites;
- the line as any direct child, not just the first.

**How readers parse the line:**

- Find the block links first, then check the grammar around them. Never split on separators, because an alias can
  contain them.
- A line containing anything other than links and separators is **malformed**: it gets a warning and no projection
  change. This protects half-typed edits that Obsidian autosaves.
- Only the line that is a direct child of a task donates edges. Nested lines belong to their own nearest task, and
  Work Log entries and fenced code never count.

**These recognisers must reject the line:**

- the hooks' sole-embed edge matcher;
- block-id-prompt's dedicated-link regex;
- navigation-hotkeys' Task Link regex;
- bob-cli's `is_section_title` and managed-log parsers.

A Depends-On line is never a Pomodoro Task Link, a dedicated Task Link bullet, a task section, or a managed log.

### 6.2 Source of truth and reconciliation

`bob task-status-hooks` applies these rules to the whole vault on every run, before Blocked derivation and inside its
existing guarded snapshot-and-retry write. Blocked in the same run therefore already sees the reconciled set.

| # | Situation for one dependent | Resolution |
| --- | --- | --- |
| R1 | Well-formed line | `[dependsOn::]` := the canonical ids of the line's resolvable task links, in line order, deduplicated by (note path, block id). A target without an `[id::]` gets its canonical id. Ids that are only in the field are **dropped and reported** (`dependency_field_ids_dropped`). |
| R2 | No line, but `[dependsOn::]` present (legacy, hand-typed, or Tasks modal) | **Adopt:** write the line from the ids that resolve to a task with a `^block-id`. Ids that don't resolve stay in the field, with a warning. |
| R3 | A link doesn't resolve, but its id (from the field) now sits on a task in another note (the task was cut and pasted) | **Heal:** rewrite the link to the new location, then apply R1. |
| R4 | A link doesn't resolve and can't be healed | Keep it verbatim and warn `unresolved_dependency_link`. It doesn't block (Tasks treats missing ids that way). Its chip shows as broken. |
| R5 | A link resolves to a block that isn't a task | Keep it, warn, and leave it out of the projection. |
| R6 | A link points to its own task | Leave it out of the projection and warn. The picker never offers it. |
| R7 | Dependency cycle | Keep Tasks semantics (every member stays Blocked). Warn `dependency_cycle` with the path. The picker refuses to create one. |
| R8 | Legacy sole `![[…]]` child whose id **is** in the field | Treat it as a dep link for one release, so a fleet with mixed versions agrees. The migration converts it. A sole embed whose id is **not** in the field is no longer an edge. |
| R9 | Label with no links | Clear the field and delete the line. |
| R10 | Malformed line, **or** the note was modified less than 2 s ago | No change. Warn or defer, extending the existing quiet interval (F12) to projection writes. |

**Rules about what the hooks may do:**

- The headless reconciler never infers a **removal** from a line that is **missing**; R2 adopts instead.
- It does infer removals from a line that is **present**. That is what lets edits in vim and by agents work.
- Every projection change appears in the JSON and human output (`dependency_projection_updates`,
  `adopted_dependency_lines`, `healed_dependency_links`, `dependency_warnings`).

**Hand edits in Obsidian:** navigation-hotkeys applies R1/R9 to the edited task block once the cursor leaves the
line, after a short debounce, so a half-typed `[[` never flips Blocked. Deleting the whole line in the editor clears
the field, because the editor can see that happen.

**The one documented surprise:** deleting the whole line *outside* Obsidian re-adopts it from the leftover field (R2).
To remove every prerequisite there, delete the links but keep the label (R9), or delete the line and the field
together.

### 6.3 Blocked, promotion, and close semantics

- **Blocked is derived exactly as before.** A task is `[?]` while any prerequisite is open, or while its `scheduled`
  date is in the future. Done and Cancelled prerequisites stop blocking (Tasks semantics); "only Done counts" would
  be a separate policy. The claim in `task-status-is-derived` still holds; only its input changes to the R1
  projection.
- **Promotion gets a new edge source.** Pomodoro roots still promote their prerequisites to Next / In Progress. The
  rules are unchanged: strongest rank wins, the queue is cycle-safe, recent-activity recovery uses the same edges, and
  dependency-promoted Next stays sticky (`task-lanes-are-sticky`). Only the edges change: the reconciled dep links
  replace "sole transcluded child". Today membership stays direct-only.
- **Closing a task never follows dependencies** (ADJ-4). `=x` embedded-tree close and the cycler's tree close keep
  following real `![[…]]` embeds, so sub-content still closes with its owner. After canonicalisation a Depends-On
  line contains no embeds, so a prerequisite can't be closed by closing something that depended on it.
- **Closed prerequisites stay on the line** as history, shown as muted chips. Unblocked doesn't mean completed, and
  dependencies don't lock completion: closing the parent by hand is still allowed.

### 6.4 The Ctrl+Shift+P "Depends on" stage

**Entry points (all open the same stage):**

| Cursor | Gesture | Edits |
| --- | --- | --- |
| A `#task` line | Ctrl+Shift+P → `dep` ↵ (the row comes first when the task already has dependencies) | This task |
| Anywhere on its Depends-On line, including inside a link | Ctrl+Shift+P | The **owning** task, skipping the property step. Never the prerequisite under the cursor. |
| A dedicated Task Link (ledger) | Ctrl+Shift+P → Depends on | The **linked** task, in its own note, named in the title (today this row is hidden) |
| A task line, counted | `N<Ctrl+Shift+P>` → Depends on | This task plus the next N, with the existing mixed `k/n` states. Ship single-task editing first. |
| A chip | `＋` / hover `×` | Opens the stage / removes that prerequisite |
| Anywhere | Palette command **Edit task dependencies** | The task under the cursor. Ship it unbound and let Bryan choose a chord (Q6). |
| Prose with several links, or a selection spanning tasks | any | Refused with a short reason. Never guess. |

**The property row** replaces today's raw `body__rahway, …` pill with a summary: `⛓ 2 · 1 open`, or `⛓ none`.
Ctrl+D on the row removes the line and the field, and recovers the parent per ADJ-8. That fixes the orphan bug in F10.

**Layout** (illustrative; it reuses the `bob-cnp` / `bid-tlp` modal styling, so it looks like `^^` and Ctrl+Shift+M
rather than a new kind of modal):

```text
╭─ ⛓ Depends on · Make appt w/ Rahway Hospital for CT scan! ────────────── body ─╮
│ ⌕ unemp▌                                                                        │
│ 1 prerequisite · 1 open · searching 844 open tasks                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│ CURRENT                                                                         │
│ ✓ [ ] Launch swarm to find hospital                 body · ^hospital-swarm   −  │
│ RESULTS                                                                         │
│   [ ] File for unemployment                         cash · ^unemployment     ＋ │
│   [*] Call unemployment office                      cash · ＋ id                │
│ ⟲ [?] Dispute North Face jacket                     cash   would create a cycle │
│ BLOCKED                                                                         │
│   [?] Rahway billing dispute                        cash   🔒 waits on 1        │
├─────────────────────────────────────────────────────────────────────────────────┤
│ ↑↓ navigate · ⇥ mark · ↵ toggle · esc dismiss                                   │
╰─────────────────────────────────────────────────────────────────────────────────╯
```

**Candidates.**

- **Pool:** every open task that passes the Tasks global filter and status registry, taken from the Tasks plugin
  cache. ledger-tools already reads it with `getTasks()` and refreshes it on `cache-update`.
  - That cache already excludes `_conflicts` (F13). Add the hooks' exclusions on top (ADJ-6).
  - Fall back to a one-time metadata-cache scan when Tasks isn't ready.
  - For notes that are open, use the editor buffer, so unsaved edits count.
  - Never read the vault from disk on a keystroke.
- **Excluded:** the task itself, and anything in fenced code.
- **Closed tasks** appear only under **Current**, so they can still be removed. Done, Cancelled, hidden, archived, and
  unresolved prerequisites stay listed there with their status and path; a missing target shows its stored id and can
  still be removed.

**Ranking.** Port the capture `:` ranker:

- every whitespace-separated term must match;
- each term scores its best tier across description, `note:blockid`, block id, note route, and section heading:
  field prefix 3, word prefix 2, substring 1, in-order subsequence 0;
- the scores are summed;
- ties keep canonical order: same note first, then In Progress, Next, Ready, with Blocked grouped beneath.

Matched characters are highlighted, and tasks with the same title are told apart by path and status. With an empty
query, the stage shows **Current**, then open tasks in the same note, then the In Progress and Next lanes. At most
about 60 rows are rendered; typing reaches the rest. Shared test vectors keep this ordering identical to Bob Mac
Capture's.

**Keys** (the existing convention, F7):

| Key | Action |
| --- | --- |
| type | Fuzzy search across the vault |
| ↑ / ↓, ^N / ^P | Move |
| ↵ | **Toggle** the highlighted row (add if absent, remove if present) and close. With marks, apply every mark. |
| ⇥ | Mark or unmark the row (`＋ add`, `− remove`, `＋ id`) and move down. Disabled in counted sessions, as today. |
| Esc | Cancel. Nothing is written and no ids are allocated. |

**Guards.** Disabled rows show their reason:

- the task itself;
- a cycle (`⟲`, with the path in a tooltip, such as "Ship → Review → Ship"). The check runs on the graph *after* the
  whole batch is applied;
- a note path the encoder can't represent;
- a target that changed since the stage opened.

Removing a link is always allowed, including an unresolved one or one in an existing cycle.

**Block IDs.** Rows whose target has no `^id` show `＋ id`. When the change is applied, today's block-ID stage opens
pre-filled with the `suggestBlockIdFromTask` slug, so ↵ accepts it. A batch prompts one target at a time.
Highlighting a row never writes an id.

**What one gesture writes:**

| Change | Line | Field / id | Dependent | Prerequisite |
| --- | --- | --- | --- | --- |
| Add | Append the link, creating the line if needed | Add the id; give the target its `[id::]` and `^id` | `[?]` if the target is open | **Commitment transfer:** if the dependent was `[*]` or `[/]`, an open target rises to at least that lane. This matches `!` today (Q3). |
| Remove | Remove the link; delete the line when it's empty | Remove the id; leave the target's `[id::]` alone | `[?]` → derived rank **now**, if no open prerequisite and no future `scheduled` date remain (ADJ-8) | unchanged |

**How the write happens:**

- Edits within one note are a single editor transaction, so one Ctrl+Z undoes the whole gesture.
- For cross-note targets, the target's id is prepared first with a preimage-checked `vault.process`, or through the
  editor if the target note is open. Then the dependent's field and line are committed together.
- If preparing the target fails, the parent is left unchanged. An unused target id is acceptable; a link pointing at
  an unprepared target is not.
- The dependent's line gets `[fresh:: today]` through `api.freshness.stampLine`, like every Ctrl+Shift+P row.

**Notices** describe the change in task terms:

- `⛓ Now waits on "File for unemployment" · Blocked`
- `⛓ No longer waits on "Launch swarm…" · Ready again`
- `⛓ 2 added · 1 removed · Blocked (1 open)`

### 6.5 Chips: what makes it beautiful

This is how a Live Preview line looks when the cursor is elsewhere. Colours come from the existing
`--task-status-*` tokens; the second chip's text is made up:

```text
[?] Make appt w/ Rahway Hospital for CT scan!                                   ⛓
    ⛓ depends on  ( ○ Launch swarm to find hospital )  ( ○ Run e2e on sase-8v ↗ sase_bug_bash )  ＋   waiting on 2
```

**Chip anatomy:**

- a miniature of the target's checkbox (`<span class="task-list-item-checkbox" data-task="…">`), coloured by
  `task-statuses.css`, so no new palette is needed;
- the cleaned description (`cleanTaskDisplayText`), cut at about 40 characters;
- `↗ note` for a target in another note;
- a tooltip with the full text, note path, status name, and `scheduled` date.

**Chip states:**

- **Open:** normal.
- **Done:** ✓, dimmed, with struck text. When more than three are done they collapse to `✓×N`.
- **Cancelled:** muted ✕, visibly different from Done.
- **Broken:** dashed, `⚠ ^id not found`.
- **Trailing summary:** `waiting on N`, or `✓ all clear`. It is never written to Markdown.

**Interaction:**

- Click opens the target (Mod-click opens a new tab) through `workspace.openLinkText`.
- Hover shows Obsidian's native page preview through `workspace.trigger("hover-link", …)`. ledger-tools already uses
  both calls for its badges.
- Hovering a chip shows a `×` that runs the remove transaction. The trailing `＋` opens the stage.
- Moving the cursor onto the line shows the raw Markdown, as Live Preview always does. Source mode stays raw.

**Implementation** in **bob-ledger-tools**, reusing the freshness-mark pipeline:

- **Live Preview:** a CM6 view plugin that scans visible ranges only and checks each line cheaply with
  `indexOf("DEPENDS ON")`.
  - Each link becomes an inline replace widget whose `eq()` is keyed on its model, so unchanged chips don't flicker.
  - Atomic ranges make each chip delete as a unit.
  - Chips must not change line height. That is the class of bug F11 had to patch for block embeds. Test Vim `j`/`k`
    across the line.
- **Reading view:** a markdown post-processor that decorates the `a.internal-link` anchors inside the line.
- **Data:** chips read only the in-memory Tasks memo; nothing is read from disk during render.
- **Accessibility:** `aria-label`s, visible focus, colour never the only signal of state, and reduced-motion support.
- **Actions:** `×` and `＋` call a small versioned **navigation-hotkeys `api` v1**
  (`openDependencyStage(ref)`, `removeDependency(parentRef, targetRef)`), following task-status-cycler's `api`
  convention. Plugins never import each other's `main.js`.
- **Mobile:** every Bob plugin manifest has `isDesktopOnly: false`, so check chip rendering and wrapping at phone
  width.

**Without the plugin**, the line still reads well: `⛓️ DEPENDS ON: ^hospital-swarm • sase_bug_bash > ^e2e-sase-8v`.
Slugged block IDs, which block-id-prompt already suggests, carry the meaning in git diffs, terminals, and
`bob capture` `task_blocks` previews. The task line keeps today's muted `[dependsOn::]` glyph; a `⛓ 1/2` mini-badge
could come later.

### 6.6 Other gestures

| Gesture | Today | Proposed |
| --- | --- | --- |
| `!` / `N!` | Toggles the embed and adds or removes a dependency | Pure transclusion toggle (ADJ-5). Refused on a Depends-On line, with a notice pointing to Ctrl+Shift+P. |
| Ctrl+Enter on a link on the line | Closes the target and strikes the link; reopening restores `![[…]]` | Closes or reopens the **target** only: no strike, no re-embed, no tree close. Dependents recover immediately, as today. |
| Strike and restore when a target closes or reopens elsewhere | Strikes `![[…]]` under `#task` lines | Skips Depends-On lines. Otherwise the reopen path would corrupt the line. |
| Alt+] / Alt+[ on the line | Cycles an embedded target | Optional: cycles the target under the cursor's link |
| Ctrl+Shift+Enter on the line | Refuses dependency embeds | Refuses the line, pointing to the stage. Otherwise it would delete one link and leave the field out of sync. |
| Ctrl+D on the Depends-on row | Deletes only the field (bug) | Deletes the line and the field, with ADJ-8 recovery |
| Ctrl+Shift+M, `move-done-tasks` | Rewrite ids and links of moved tasks | Unchanged, plus: rewrite same-note `[[#^x]]` links *inside* a moved block whose target stayed behind to include the note name |
| "Rewrite dependency navigation links" and `migrate-dependency-bullets.mjs` | Emit embeds | Delete the command, and replace the script with the migration in §7. **Don't run either unchanged.** |
| `bob capture` / Bob Mac Capture | No dependency grammar | Unchanged; the line shows as an ordinary child in previews. Any future capture syntax for dependencies lands in bob-cli first (`mac-capture-is-a-thin-client`). |

### 6.7 Memory drafts (write through `/sase_memory_write` when the feature ships, not before)

**New glossary strand `glossary/task-dependency-link.md`.** Keyword: **Task Dependency Link**; aliases: **task dep
link**, **dep link**.

> A plain (never transcluded) [[glossary:task-link]] to a prerequisite of another Obsidian task. A task's dep links
> all sit on its Depends-On line, its first direct child: `⛓️ **DEPENDS ON:** [[#^a]] • [[note#^b]]`. That line is
> the source of truth: Bob derives the task's `[dependsOn::]` field and each target's `[id::]` from it, and the task
> stays Blocked `[?]` while any target is open. Linking the dependent under today's Pomodoros raises its open
> prerequisites to Next. Add or remove dep links with Ctrl+Shift+P → **Depends on**, which fuzzy-searches open tasks
> across the vault, or by editing the line. A dep link is a prerequisite, not a sub-task: closing the dependent never
> closes its targets, and dep links never count as Pomodoro Task Links.

Keep the syntax details, key tables, and repair rules in `docs/task-dependencies.md`, not in the glossary.

**Amend `glossary:task-link`.** Replace "As another special case, transcluded task links that are the only contents of
a sub-bullet on another Obsidian task are treated as sub-tasks (i.e. dependencies) of that task" with "Task Links on a
task's Depends-On line are [[glossary:task-dependency-link]]s." Leave the Pomodoro sentence as it is.

**New decision record, "Task Dependencies Are Links On One Depends-On Line":**

- **Applies to:** bob-cli, bob-plugins, the vault.
- **Claim:** §6.1–6.3 in one paragraph.
- **Why:** §2.
- **Rejected:** links only; fields only with a virtual line; a field-authoritative generated line; one bullet per
  dependency; links on the task line itself; the Tasks modal as the editor; `!` as the gesture; stored aliases and
  strikes.
- **Cost:**
  - four parsers kept in sync by shared vectors;
  - the projection exists at all;
  - deleting the whole line outside Obsidian is re-adopted;
  - dependency edits made in the Tasks modal to a task that has a line are dropped;
  - `#^ref` embeds no longer promote.
- **Reopens when:**
  - the projection drifts in practice (R1/R2 warnings on most hooks runs for two weeks);
  - the Tasks modal becomes a real editing surface;
  - Tasks' `is blocked` stops being load-bearing.

Follow the supersession convention: mark only what this retires. It updates the "transcluded dependency path" wording
and the `!` removal rationale in `task-status-is-derived`; that record's Blocked rule still stands.

---

## 7. Delivery

### 7.1 Phases

| Phase | Repo | Work | Size |
| --- | --- | --- | --- |
| P0 Contract | bob-cli | <ul><li>`docs/task-dependencies.md`: grammar, R1–R10, gestures.</li><li>Shared conformance vectors for parsing, canonical writing, R1–R10 outcomes, and the ranker. Rust and three JavaScript plugins consume them, following the Today / walk-vector pattern.</li></ul> | S |
| P1 Hooks | bob-cli | <ul><li>A `task_dependencies` module: a parser reusing `block_link_occurrences` and a writer reusing freshness field placement.</li><li>R1–R10 reconciliation before Blocked, with the quiet-interval guard.</li><li>Promotion edges from the reconciled set; legacy embeds read through R8.</li><li>Make `is_section_title` and the managed-log parsers ignore the line.</li><li>Additive JSON and human output; docs and `--help`.</li></ul> | M |
| P2 Stage and writers | bob-plugins: navigation-hotkeys | <ul><li>The vault-wide stage (§6.4) and the single add/remove transaction.</li><li>Entry points from the line and from Task Links.</li><li>The Ctrl+D fix, the hand-edit mirror, `!` decoupled, and `api` v1.</li><li>Delete the legacy consolidate code once migration is done.</li></ul> | L |
| P3 Compatibility | task-status-cycler, block-id-prompt | <ul><li>Skip strike and restore on the line; tree close ignores it.</li><li>Ctrl+Enter never re-embeds; Ctrl+Shift+Enter refuses the line.</li><li>The id normalizer learns about the line.</li><li>Optionally, `api.recoverBlockedTasks(parents)` for ADJ-8.</li></ul> | M |
| P4 Chips | bob-plugins: ledger-tools | <ul><li>Live Preview and Reading view chips.</li><li>CSS built on `--task-status-*` tokens.</li><li>Render vectors.</li></ul> | M |
| P5 Migration | bob-plugins script + vault | Dry-run first (§7.2). **Run only after P1–P4 are deployed on every machine.** | S |
| P6 Publish and clean up | bob-cli memory, all | <ul><li>Publish the glossary strand, the `task-link` amendment, and the decision record with P5.</li><li>Stop reading legacy embeds one release later.</li></ul> | S |

### 7.2 Migration

- **Convert:**
  - the 38 live dependency embeds and 5 struck links into Depends-On lines on their parents;
  - the field-only parents, through R2.
  - Only embeds whose target id **is in** the parent's `dependsOn` are converted.
- **Leave alone:**
  - the 21 `#^ref` embeds;
  - Pomodoro ledger embeds in daily notes;
  - Work Logs, fenced examples, and any child that has other content beneath it. That last case is reported as a
    conflict, not flattened.
- **Preserve:** indentation, CRLF line endings, and final-newline state.
- **Before writing:**
  - cross-check with `bob task-status-hooks --dry-run --format json` before and after. There should be no Blocked
    flips, and rank edges should only change for the 21 `#^ref` embeds;
  - a second run must change nothing.
- **Expected run:** about 18 notes changed.
- **Commit:** in the vault, following the vault's `AGENTS.md`.

### 7.3 Rollout order

1. P1 on every machine, reading **both** formats.
2. P2–P4 everywhere, with `bob plugins sync` run from the linked bob-plugins checkout.
3. P5.
4. Remove legacy embed reading after one release.

If the vault is migrated before step 1 reaches the MacBook, its old hooks lose the promotion edges. Blocked survives,
because it comes from the fields.

### 7.4 Acceptance checks

| Area | Cases |
| --- | --- |
| Ownership | Task line; its Depends-On line (cursor inside a link); a nested task; a ledger Task Link; an ambiguous selection |
| Parser | Same-note, basename, and full-path links; aliased, struck, and embedded inputs; a separator inside an alias; fenced code; a malformed or half-typed line; legacy 🔗 / `DEPENDENCIES` |
| Reconciler | R1–R10 outcomes; idempotence; quiet-interval deferral; no removal inferred from a missing line; output counts |
| Stage | Vault-wide results; ranking parity with capture `:`; Tab-mark batch; removing a done, cancelled, hidden, or missing prerequisite; cycle and self rows; the `＋ id` prompt; Esc changes no bytes; one undo step; unsaved buffer in another note; a target edited mid-prompt |
| Semantics | AND blocking; schedule plus dependency; immediate recovery on removal; commitment transfer; strongest-rank promotion along chains; closing a dependent never closes prerequisites; `#^ref` embed no longer an edge |
| Gestures | `!` refused on the line; Ctrl+Enter closes the target without re-embedding; Ctrl+Shift+Enter refused; Ctrl+D removes the line and field; Ctrl+Shift+M / `move-done-tasks` keep the line with its task |
| Rendering | Live Preview, Reading view, and Source mode; native hover and click; narrow and mobile widths; light and dark themes; Vim `j`/`k` across chips; screen-reader labels |
| Pilot | Bryan adds prerequisites from two projects, removes a completed one, follows a link, and edits while another note has unsaved changes. Count keystrokes and mistakes against today's flow. |

---

## 8. Risks and open questions

| Risk | Mitigation |
| --- | --- |
| Four parsers (Rust, navigation-hotkeys, ledger-tools, block-id-prompt) drift apart | One grammar document plus shared vectors |
| The projection is still a second representation | One authority, writers that update both together, an idempotent reconciler with reported counts, and a reopen trigger in the decision record |
| The hooks now write `[id::]` in other notes | The same guarded pipeline: snapshot, byte re-check, quiet interval, recovery copies. Dry-run shows every write. |
| Hand edits flip Blocked mid-typing | The editor mirror runs when the cursor leaves the line; the hooks skip malformed lines and recently modified notes |
| A third format change in fourteen weeks | Keep what made embeds attractive: live status (chips) and acting in place (Ctrl+Enter on a link). Migration waits for chips. |
| Chips cost editor stability | Inline, fixed-height widgets limited to visible ranges, with a Vim navigation test |

**Questions for Bryan:**

- **Q1.** Should `#^ref` reading-task embeds keep promoting their reading task when the parent is linked today?
  *Recommendation: no.* They are content. If you want that behaviour, make the reading task a dep link.
- **Q2.** Is the label with ⛓️ and ` • ` right, or do you prefer the legacy 🔗? *Recommendation: ⛓️* (rollout safety,
  §3).
- **Q3.** Should adding a dependency in the picker transfer the dependent's Next / In Progress lane to the
  prerequisite, as `!` does today? *Recommendation: yes.* Otherwise a Pending task's commitment quietly vanishes when
  it becomes Blocked.
- **Q4.** Should a reverse "Blocks…" stage (pick tasks that should wait on *this* one, like Tasks' "After this") ship
  in P2? *Recommendation: later.* It writes to other tasks' lines and is less common.
- **Q5.** Do you ever edit dependencies with the Obsidian Tasks modal? If so, the authority choice should flip to the
  field (§3, first row).
- **Q6.** Which chord, if any, should the direct "Edit task dependencies" command get? `hotkeys.json` shows no user
  binding on Ctrl+Shift+B or Ctrl+Shift+L, but I didn't audit plugin-declared defaults.

---

## 9. Problems found along the way (independent of this redesign)

1. **task-status-cycler:** Alt+] / Alt+[ to Done or Cancelled skips `finalizeClosedTasks`, so Blocked dependents
   only recover on the next hooks run. cld filed bead `bob-cli-3k`.
2. **navigation-hotkeys:** Ctrl+D on `dependsOn` orphans the embeds and leaves the parent `[?]`. P2 fixes it.
3. **navigation-hotkeys:** "Rewrite dependency navigation links (current note)" can delete cross-note embeds. Until
   P2 removes it, avoid it on notes with cross-note dependencies.
4. **navigation-hotkeys:** the picker badge shows the path-encoded id (`^projects__Here__x`) instead of the block id.
5. **`move-done-tasks`:** same-note `[[#^x]]` links inside an archived block can dangle when `^x` stays behind.
6. **The `dependsOn` hooks:** the dependency graph is built from embed shape, not from `dependsOn` (F2). So the 21
   `#^ref` embeds promote reading tasks today, which is probably unintended.

---

## 10. Recommended solution

**Replace transcluded dependency sub-bullets with task dependency links on one managed Depends-On line. Make the line
the source of truth, edit it from a vault-wide Ctrl+Shift+P stage, and draw it as live status chips.**

1. **Format (ADJ-2).**
   - Each dependent gets one first-child line: `- ⛓️ **DEPENDS ON:** [[#^a]] • [[note#^b]]`.
   - It holds the shortest plain block links, separated by ` • `, with no aliases, strikes, or embeds.
   - It may wrap. An empty line is deleted.
2. **Authority (ADJ-1).**
   - The line is the truth. `[dependsOn::]` / `[id::]` remain as its derived index for Tasks' `is blocked`.
   - Every writer updates both in one transaction.
   - `bob task-status-hooks` reconciles the whole vault (R1–R10): it projects, adopts dependencies that exist only in
     the field, heals moved targets through `[id::]`, skips malformed or recently modified notes, and warns about
     broken links and cycles.
3. **Semantics (ADJ-4, ADJ-8).**
   - Blocked stays derived, now from the projection, and promotion follows the same edges.
   - Dependencies are prerequisites, never sub-content: closing a dependent never closes them, and `#^ref` embeds
     stop being edges.
   - Adding a dependency blocks the dependent and transfers its lane. Removing one unblocks it immediately when
     nothing else blocks it.
4. **Editing (ADJ-6, ADJ-7).**
   - Ctrl+Shift+P → **Depends on** opens a stage that fuzzy-searches every eligible open task in the vault, ranked
     like bob's capture `:` picker, with current dependencies pinned at the top.
   - ↵ toggles, ⇥ marks several, and ↵ then applies them.
   - Cycles and self-links are refused with a reason, and block IDs are created in place.
   - The same stage opens from the Depends-On line, from a Task Link, counted, from chip `＋`/`×`, and from a
     bindable command.
   - Ctrl+D removes the dependency list cleanly. `!` goes back to being only a transclusion toggle (ADJ-5).
5. **Beauty (ADJ-3).**
   - ledger-tools draws each dep link as a chip in Live Preview and Reading view: the target's real checkbox and
     colour, its live description, `↗ note` for other notes, native click and hover preview, `×` / `＋`, and a
     `waiting on N` / `✓ all clear` summary.
   - Without the plugin, the line is still readable.
   - **The vault migration waits for chips.**
6. **Vocabulary (ADJ-10).** Add `glossary:task-dependency-link` ("task dep link"), amend `glossary:task-link`, and
   record the decision. Publish all three alongside the migration.
7. **Delivery.**
   - P0 contract and vectors → P1 hooks, reading both formats, on every machine → P2 stage → P3 compatibility → P4
     chips → P5 dry-run-first migration of about 44 tasks in about 18 notes → P6 publish and remove legacy reading.
   - Defer the path codec (ADJ-9); no active note needs it today.

---

## Sources

**Peer reports (this directory):**

- `__cdx`: authority rules, safety, identity analysis, acceptance matrix;
- `__cld`: consumer matrix, census, history, R-table, stage and chip design;
- `__grk`: live blocked set, Sub-projects precedent, `#^ref` separation, gesture critique;
- `__mus`: hooks code path and rollout ordering;
- `__gem`: alias argument and the embed viewport and Vim commits.

**bob-cli `8f01f33`:**

- `src/native/task_status_hooks/references.rs:307–383` (`dependency_edges`)
- `src/native/task_status_hooks/sync.rs:678` (`task_dependency_states`)
- `src/native/task_status_hooks/parse.rs:38`, `src/native.rs:3` (excluded directories)
- `src/native/capture_pomodoro_close/linked_tasks.rs:540–620, 1189` (embedded tree close)
- `src/native/capture_link_tasks.rs:256` (`rank`)
- `docs/task-status-hooks.md:655–672` (quiet interval)

**bob-plugins `ede89d3`:**

- `plugins/bob-navigation-hotkeys/main.js:241–267` (grammar), `:1433` (formatter), `:22178–22282` (local stage and
  hints), `:22803` (`chooseTaskDependency`), `:25237` (consolidate command)
- `plugins/bob-ledger-tools/main.js:3012, 3093` (`_conflicts` exclusion)
- all plugin `manifest.json` files (`isDesktopOnly: false`)
- commits `982ac8b`, `d33c4a6`, `5337f45`, `30ae7b9`

**Vault `8d80e01a`:**

- `.obsidian/hotkeys.json` (Ctrl+Shift+P → `set-bullet-property`)
- `.obsidian/snippets/dataview-properties.css:134–170`
- Sub-projects rows in `bob.md` and `sase_art.md`
- path and dependency census over active notes; `_conflicts/` contents

**Memory:**

- `glossary:task-link`
- `decisions:task-status-is-derived`
- `decisions:task-lanes-are-sticky` (read with `sase memory read`)

**Upstream** (cited by cdx and cld):

- Obsidian internal links, block links, and hover preview
- Obsidian editor extensions and Markdown post-processing docs
- Tasks "Task Dependencies" and `Task.isBlocked()` (missing ids don't block)
