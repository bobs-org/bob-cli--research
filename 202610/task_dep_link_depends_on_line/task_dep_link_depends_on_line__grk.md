# Task dep links: compact wikilinks, one managed line, vault-wide picker

## Bottom line

This is a good idea, and the vault already invented most of it. Stop using
**transclusions** as the human face of task dependencies. Keep
`[dependsOn:: …]` as the machine source of truth for Blocked (and, after a
small hooks change, for Next-promotion too). Show those same blockers as
**ordinary Task Links on one managed child bullet**, in the visual language
the vault already uses for sub-projects:

```markdown
- [?] #task Make appt w/ Rahway Hospital for CT scan! [dependsOn:: body__hospital-swarm] ^rahway
	- 🔗 **DEPENDS ON:** [[body#^hospital-swarm]]
	- **PHONE NUMBER:** (732) 381-4200
```

Add and remove those links through a **vault-wide fuzzy task picker**.
`Ctrl+Shift+P` → Depends on is the discoverable path (the current
`local_task_id` row, expanded beyond the current file). Bare `!` on the
parent task opens the same picker; it is the one-chord path. Both write the
bullet and the Dataview field together.

Do **not** drop `[dependsOn::]`, do **not** treat every `![[…]]` under a
task as a dependency (reading-material embeds stay), and do **not** make
`Ctrl+Shift+P` the only gesture. Those are the adjustments that make the
request reliable.

Live on 2026-10-02 the change is small: **13** open Blocked tasks, all
dependency-blocked; **44** tasks carry `dependsOn` (24 of them already
done); **57** sole transclusion children sit under `#task` lines in 23
active notes. A one-shot migration can collapse the dependency transclusions
onto the managed line and leave reading-material embeds alone.

## The question

Bryan currently encodes “B must finish before A is unblocked” by putting a
**transcluded** task block link as a sub-bullet of A:

```markdown
- [?] #task Make appt w/ Rahway Hospital for CT scan! [dependsOn:: body__hospital-swarm] ^rahway
	- ![[#^hospital-swarm]]
```

He wants to:

1. Use **normal** (non-embed) Task Links for this.
2. List **every** dependency on **one** visually appealing line.
3. Make add/remove easy from the currently selected task, including tasks in
   any area/project note, with **vault-wide fuzzy search**. He nominated
   `Ctrl+Shift+P`, which already has a `dependsOn` row.
4. Add a glossary term **task dependency link** / **task dep link**.
5. Have research lead the design: intuitive, reliable, beautiful.

This report critiques that plan, names justified requirement changes as
**ADJ-n**, and recommends an implementation that fits contracts already in
bob-cli, bob-plugins, and the Bob vault.

## What is already true

Measured 2026-10-02 against `~/bob`, `docs/task-status-hooks.md`,
`docs/dataview.md`, `docs/freshness.md`, `docs/projects.md`, glossary
`task-link`, decisions `task-status-is-derived` / `task-lanes-are-sticky`,
bob-navigation-hotkeys 1.50.0, block-id-prompt 1.17.0, task-status-cycler
1.19.0, and `~/.config/bob/config.yml`.

| # | Fact | Evidence |
| --- | --- | --- |
| E1 | A Task Link is a block link to an Obsidian task. Glossary today special-cases **transcluded** sole child bullets of a `#task` as sub-tasks / dependencies, and sole child bullets of a Pomodoro as logged work. | `glossary:task-link` |
| E2 | Blocked `[?]` is derived from Dataview `[dependsOn::]` (and future `scheduled`). It is **not** derived from the child bullets. Tasks IDs are vault-wide `note-path-with-slashes-as-__` + `__` + block id (`projects__Shared__review`). | `decisions:task-status-is-derived`; `docs/task-status-hooks.md` “Derived Blocked Status”; `docs/dataview.md` |
| E3 | Next-promotion **is** derived from those child bullets: `bob task-status-hooks` walks **sole transcluded** block-link children of a linked task and promotes them monotonically (`[ ] < [*] < [/]`). Sticky lanes keep that Next. | `docs/task-status-hooks.md` “Sync rules”; `README.md` “Sole transcluded dependencies inherit the strongest parent rank” |
| E4 | The plugin already keeps **two** writings in sync when `!` or the `dependsOn` row runs: `[dependsOn:: id]` on the parent, and one transclusion child per dep (`\t- ![[note#^id]]`). Removing a transclusion with `!` is status-neutral for Blocked; hooks have the last word. | bob-navigation-hotkeys `setLocalTaskDependency`, `planDependencyNavigationBulletSync`; `decisions:task-status-is-derived` |
| E5 | A **single-line** managed bullet already exists in the parser, as the *legacy* shape the plugin still recognizes so it can migrate *away* from it: ``- 🔗 **DEPENDS ON:** [[#^a]] • [[#^b]]``. New writes emit one transclusion per dep. `DEPENDENCY_NAVIGATION_LINK_RE` only captures **same-note** `[[#^id]]`. | `plugins/bob-navigation-hotkeys/main.js` lines 241–266, `formatDependencyNavigationBulletWithMarker`; `scripts/migrate-dependency-bullets.mjs` |
| E6 | `Ctrl+Shift+P` already has a `dependsOn` property (`values: local_task_id` in `~/.config/bob/config.yml`). That picker lists **open `#task` lines in the current file only**. On a dedicated Pomodoro Task Link the row is **hidden** (“remote tasks are edited through their own notes, never via dependency transclusion”). | `config.yml` lines 9–10; `createBulletPropertyLocalTaskItems`; `createLinkPickerPropertyItems` |
| E7 | Bare / counted `!` in Vim normal mode does **not** open a picker. It toggles embed markers on block links already on the current line, then syncs `[dependsOn::]` when the parent is a `#task`. Empty current line → `!` falls through to Vim. | `handleCountedTransclusionToggle`, `findTransclusionToggleTargets` |
| E8 | Vault-wide fuzzy task search already exists: block-id-prompt’s `^^` Task Link picker (`TaskLinkPickerModal`, `fuzzyIncludes`, Unblocked / Blocked groups, skips `#hide`). Navigation pickers use subsequence `fuzzyMatchesText` on the same `bob-cnp-*` modal. | block-id-prompt `main.js` / `styles.css`; navigation `FilteredPickerModal` |
| E9 | `[id::]` is hidden in Live Preview; `[dependsOn::]` is a muted glyph. The 2026-07-16 plan that did this called the field a duplicate of “the transcluded block links rendered directly beneath the task.” | `plan:202607/hide_deterministic_task_fields.md` |
| E10 | Ctrl+Enter on an **embedded** Task Link closes the transcluded source tree. Ctrl+Shift+Enter **refuses** to delete a sole transclusion child of a `#task` (`Task link is a sub-task dependency; edit dependencies instead`). | task-status-cycler; block-id-prompt `isDependencyTransclusionLink` |
| E11 | Project notes already use the compact one-line link row Bryan wants, for sub-projects: ``- 🧩 **Sub-projects:** [[a]] • [[b]] • [[c]]``. Schedule Log / Work Log use the same managed-marker grammar (`🗓️ **SCHEDULE LOG**`, `🛠️ **WORK LOG**`). | live `sase.md` L12; `glossary:work-log`; navigation managed-log regexes |
| E12 | Obsidian block embeds are **block-level**. `![[a]] ![[b]]` on one source line still renders as stacked embeds, each expanding the target’s full list subtree (Work Log, Schedule Log, nested deps). That is a platform constraint, not a CSS gap. | Obsidian embed rendering; live `body.md` `^rahway` transcludes `^hospital-swarm`, which itself owns a four-entry Schedule Log |
| E13 | Live vault, 2026-10-02, `bob query` (native Tasks): 3238 globally-filtered tasks, **844** not done, **13** `is blocked` (all 13 have open `dependsOn`; 0 are schedule-only), **44** tasks with a non-empty `dependsOn` (status mix: 14 `?`, 24 `x`, 6 `-`), **9** `is blocking`. Typical arity is **one** dep (max 2). | `bob query --tasks` |
| E14 | Cross-note deps already exist and the local picker cannot author them. Example: `sase_agents_repo.md` “Start adding `sase--<name>` badges…” `[dependsOn:: sase_bug_bash__e2e-sase-8v]` with child `![[sase_bug_bash#^e2e-sase-8v]]`. | live `sase_agents_repo.md` L26–28 |
| E15 | Sole transclusions under `#task` are a **mixed bag**. Active vault: **57** under `#task` (23 files), **213** under Pomodoros, **11** other. Several under-task embeds are reading material with **no** `dependsOn`, e.g. `sase_dyn_agent_fam.md` “Read dynamic agent family critique!” → `![[ref/chat/…#^ref]]` ×2. Zero remaining `🔗 **DEPENDS ON:**` bullets. Zero plain (non-embed) sole child block links under `#task`. | walk of `~/bob` excluding `.obsidian` / `_templates` / `_generated` / `done/` |
| E16 | Chip language is already designed: `.bob-plan-chip` / `.bob-nh-notice-chip` / `.bob-cnp-status-pill` / `.bob-fresh-mark`, all `color-mix` on `--task-status-*` tokens. Freshness marks prove Live Preview can replace a Dataview pill with a compact widget while the Markdown stays the source of truth. | bob-ledger-tools `styles.css`; bob-navigation-hotkeys `styles.css` |

### Live blocked set (2026-10-02)

All 13 are dependency-blocked. Files: `cash.md` (6), `body.md` (2),
`job.md` (2), `sase_toobig_symvision.md` (2), `sase_agents_repo.md` (1).
Shared blockers (`cash__unemployment`, `job__update-goog-end-date`) already
fan out to several parents — the one-line form will usually hold a single
link, occasionally two.

## Critique of the request

The direction is right. Transclusions were a local maximum: they show the
live task text and checkbox, and Ctrl+Enter can close the source from the
embed. They fail the new requirements on purpose.

**One line is incompatible with transclusion.** Embeds render as blocks.
The current writer already emits **one bullet per dependency**
(`formatDependencyNavigationBulletWithMarker` joins with `\n`). Putting
`![[a]] ![[b]]` on one line would still stack two full task trees. The
legacy `🔗 **DEPENDS ON:** [[#^a]] • [[#^b]]` bullet is the format that
actually satisfies “all dependency task links on a single line.” The 2026-07
migration walked **away** from that format to get live preview of each
blocker. This request walks back, with better search and cross-note links.

**Transclusions are noisy in the notes that matter.** `body.md` `^rahway`
transcludes `^hospital-swarm`. That target carries a reschedule note and a
four-entry Schedule Log. Live Preview inlines all of it under a CT-scan
appointment. Compact links plus a chip (or an alias) keep the outline
readable.

**The dual graph is the reliability bug.** Blocked reads `[dependsOn::]`.
Promotion reads sole transclusions. The plugin reconciles them only when `!`
or the local picker runs. Hand-authored `![[note#^id]]` without `!`, or a
`dependsOn` edit without a child bullet, drifts. Hooks will Block from the
field and promote from the bullet, so the two views of “what is this waiting
on?” disagree. Unifying both consumers on `[dependsOn::]`, and treating the
child line as a synchronized projection, removes that class of bug.

**`Ctrl+Shift+P` already “supports” dependencies in the weakest way.** The
row is real, and it does write both the field and a navigation bullet. It
only sees **this file**, it is hidden in Task Link mode, and `local_task_id`
never prompts across the vault. The pain Bryan is naming is exactly
`sase_agents_repo` → `sase_bug_bash#^e2e-sase-8v`: a cross-note blocker the
property picker cannot add. Vault-wide search is the actual UX gap;
`Ctrl+Shift+P` is one door into it.

**`!` is muscle memory for dependencies, and it is the wrong tool after this
change.** Today it means “toggle embed on the links under the cursor.” Once
embeds are no longer the dep representation, that chord should open the
picker (parent task) or remove the link under the cursor (managed bullet).
Dropping `!` and forcing `Ctrl+Shift+P` → Depends on → search is three
keystrokes for a daily edit.

**Not every transclusion under a task is a dependency.** “Read this
critique” tasks embed `ref/chat/…#^ref` as the work product. A migration or
hooks walker that treats every sole `![[…#^id]]` child as a Task Dep Link
would steal those. The managed `🔗 **DEPENDS ON:**` marker is what makes
the two kinds distinguishable.

**Dropping `[dependsOn::]` would break Blocked, dash `is blocked`, Tasks
parity, and `bob query`.** The field is ugly (that is why it is a glyph)
and it must stay. Task dep links are the human face; the field is the
index.

## Adjustments to the requirements

These change the prompt. Each is a requirement I would add or rewrite
before implementation.

**ADJ-1. `[dependsOn::]` stays the machine source of truth.** Task dep
links never replace it. Every add/remove rewrites **both** the managed
bullet and the field, including `[id::]` on the target when missing. Hooks
remain the vault-wide reconciler for Blocked.

**ADJ-2. Promotion walks `dependsOn`, not transclusions.**
`bob task-status-hooks` already parses vault-wide IDs for Blocked. Use that
same index for the Next/In-Progress inheritance graph. Sole transclusion
children stop being edges. Reading-material embeds and Pomodoro Task Links
are then incapable of accidentally promoting a `^ref` block.

**ADJ-3. One managed child bullet, not “any normal task link nearby.”**
A free `[[note#^id]]` under a `#task` is ambiguous (citation, related work,
future Task Dep Link). Canonical shape:

```markdown
	- 🔗 **DEPENDS ON:** [[note#^block]] • [[other#^block]]
```

Same grammar as today’s legacy parser (`DEPENDENCY_NAVIGATION_LABEL`,
`DEPENDENCY_NAVIGATION_EMOJI`, `DEPENDENCY_NAVIGATION_SEPARATOR`), extended
to **cross-note** `[[note#^id]]` (the current regex is same-note only).
Indent and list marker stay as they are for Schedule Log. When the list is
empty, the bullet is deleted.

**ADJ-4. Do not convert reading-material transclusions.** Migration and
hooks touch a child `![[…#^id]]` only when that target’s vault-wide id is
in the parent’s `[dependsOn::]`. Other embeds stay.

**ADJ-5. `Ctrl+Shift+P` is required and not exclusive.** Stage 1 still
lists Depends on (defined rows first, with a count, e.g. `Depends on · 2`).
Stage 2 is the vault-wide picker. Bare `!` on a `#task` parent opens that
same stage-2 modal. `N<Ctrl+Shift+P>` → Depends on still applies one pick
to the counted parents. Task Link mode **shows** the row and writes the
remote note (today it hides it).

**ADJ-6. The picker is vault-wide with same-note bias, not a new search
stack.** Reuse block-id-prompt’s open-task corpus and grouping (Unblocked,
then Blocked; skip `#hide`; skip self). Rank: already-linked → same note →
other notes. Filter with the existing subsequence fuzzy matcher against
title, note basename, `^block-id`, and `id`. Offer closed tasks **only**
when they are already linked, so they can be removed. Enter toggles
immediately and leaves the modal open (add three deps without a commit
step). Esc closes. A missing `^block-id` on an added target still runs the
existing block-id prompt and writes the canonical `[id::]`.

**ADJ-7. Beauty is a Live Preview chip row on top of the managed bullet,
plus short aliases in the source.** Transclusion was doing “show live title
and status.” Replace that with:

- Source / Reading / graph: ``[[cash#^unemployment|File for unemployment]]``
  (alias = cleaned task display text, truncated). Plugin refreshes aliases
  on add/remove and hooks may refresh them when it repairs the bullet.
- Live Preview: a CodeMirror decoration in the freshness-mark style, one
  chip per link, accented with `--task-status-*` (Ready blue, Next green,
  Pending orange, Blocked rose, Done muted + struck). Hover: native page
  preview. Click: open the target. Hover-`×` on a chip removes it. A
  trailing `+` chip opens the picker.

If the decoration is off, the Sub-projects-style line is still the fallback
and still looks like the rest of the vault.

**ADJ-8. Preserve close-from-the-link.** Ctrl+Enter on a Task Dep Link
(plain, on the managed bullet) closes the **target** task and recovers
Blocked dependents, matching today’s embed behavior. Ctrl+Shift+Enter on
that bullet still refuses “delete this link” and points at `!` /
`Ctrl+Shift+P`.

**ADJ-9. Glossary: add Task Dep Link; retarget Task Link.** The new strand
is the human-facing term. The Task Link strand drops the sentence that
transcluded children are dependencies, and points at Task Dep Link instead.
Pomodoro Task Links stay a Task Link special case.

## Alternatives considered

| Option | What it is | Why it loses |
| --- | --- | --- |
| A. Keep per-dep transclusions, restyle them | CSS to shrink embeds | Embeds are still blocks; nested logs still expand; cannot share a line; still collides with reading-material embeds |
| B. Links only, drop `[dependsOn::]` | Human links are the only graph | Breaks Tasks `is blocked`, dash, `bob query`, identity migration, Blocked derivation |
| C. Field only, no child bullet | LP widget injected under the parent, zero extra Markdown | Source mode, git diff, backlinks, and graph go blind; Bryan asked for normal Task Links |
| D. Inline links on the parent line | `- [?] #task Ship [[a]] [[b]] [dependsOn::] ^ship` | Fights `fresh` / `scheduled` / `id` / `^block`; Tasks description absorbs the wikilinks; no managed marker |
| E. `Ctrl+Shift+P` only, retire `!` | One discoverable chord | Three-step daily edit; throws away the chord already bound to dependencies |
| F. Vault-wide picker as a new keymap | e.g. `Ctrl+Shift+D` | Adds a chord the user did not ask for; `Ctrl+Shift+P` already owns `dependsOn` |
| G. Same-note picker + hand-typed cross-note | Status quo plus docs | The actual gap is `sase_agents_repo` → `sase_bug_bash`; local_task_id cannot express it |

## Recommended solution

### 1. Vocabulary

**Task Dep Link** (aka **task dependency link**): a Task Link that names a
blocker of another `#task`. Task dep links are ordinary (non-transcluded)
block links collected on one managed child bullet of the parent:

```markdown
	- 🔗 **DEPENDS ON:** [[cash#^unemployment]] • [[sase_bug_bash#^e2e-sase-8v]]
```

They are the human-facing form of the parent’s `[dependsOn::]` list. Adding
or removing one through `Ctrl+Shift+P` or `!` rewrites the bullet and the
Dataview field together. They are distinct from Pomodoro Task Links (those
live under a Pomodoro) and from reading-material transclusions.

Proposed `glossary/task-dep-link.md`:

```markdown
---
keyword: Task Dep Link
aliases:
  - "task dependency link"
---

A [[glossary:task-link]] that names a blocker of another `#task`. Task dep
links are ordinary (non-transcluded) block links collected on one managed
child bullet of the parent, in the shape `🔗 **DEPENDS ON:** [[note#^id]] •
[[other#^id]]`. They are the human-facing form of the parent's
`[dependsOn::]` list: adding or removing one through Ctrl+Shift+P or `!`
rewrites both the bullet and the Dataview field together. Blocked `[?]` and
Next-promotion read the field, not the bullet. They are not Pomodoro Task
Links, and they are not reading-material transclusions under a task.
```

Task Link strand: delete “transcluded task links that are the only contents
of a sub-bullet on another Obsidian task are treated as sub-tasks”; add a
sentence that those relationships are Task Dep Links.

A later `decisions:` record is warranted once the plan is accepted
(“Blocked and promotion share `dependsOn`; the managed bullet is a
projection”). Out of scope for this research write.

### 2. Source of truth and projection

```
[dependsOn:: body__hospital-swarm, sase_bug_bash__e2e-sase-8v]   ← machine
	- 🔗 **DEPENDS ON:** [[body#^hospital-swarm]] • [[sase_bug_bash#^e2e-sase-8v]]  ← human
```

Invariant: the set of resolved vault-wide IDs in the field equals the set of
resolvable Task Dep Links on the managed bullet. `!`, `Ctrl+Shift+P`, and
`bob task-status-hooks` all restore the invariant. Hand edits to one side
are repaired on the next hooks run (sibling of marker repair / empty
Pomodoro cleanup), with a warning when an id does not resolve.

### 3. Gestures

| Cursor | Chord | Result |
| --- | --- | --- |
| `#task` parent | `Ctrl+Shift+P` → Depends on | Vault-wide picker (ADJ-6) |
| `#task` parent | `!` | Same picker, no stage-1 hop |
| Managed DEPENDS ON bullet, on a link | `!` | Remove that one Task Dep Link |
| Counted parents | `N<Ctrl+Shift+P>` → Depends on | One pick, applied to each parent |
| Pomodoro Task Link | `Ctrl+Shift+P` → Depends on | Picker writes the **remote** parent (row no longer hidden) |
| Managed DEPENDS ON bullet | Ctrl+Enter | Close the target (ADJ-8) |
| Managed DEPENDS ON bullet | Ctrl+Shift+Enter | Refuse; notice names `!` / `Ctrl+Shift+P` |

`^^` stays “insert a Task Link” (Pomodoro logging, citations). If the user
inserts a Task Link as a child of a `#task` and then presses `!` on that
line, the plugin **promotes** it onto the managed bullet (the expert path
that today’s transclusion toggle occupies).

### 4. Picker appearance

Reuse `bob-cnp` / `bid-tlp` chrome so it feels like `^^` and
`Ctrl+Shift+M`, not a third modal family.

```
┌ Depends on — cash.md · Dispute North Face jacket ─────────┐
│ 🔍 unemployment                                           │
│ Linked  1 · same note  4 · vault  12                      │
│ ✓  [?]  cash.md   File for unemployment     ^unemployment │
│    [ ]  cash.md   Call about unemployment   ^call-real-id │
│    [*]  job.md    Update Google end date    ^update-goog  │
│ Blocked                                                       │
│    [?]  body.md   Rahway CT scan            ^rahway       │
│ ↵ toggle · esc close                                      │
└───────────────────────────────────────────────────────────┘
```

Linked rows carry a check and sort first. Same-note rows outrank other
notes. Status pills use the existing `taskStatusClass` tokens. Subtitle is
the parent task, truncated with `truncateBulletPropertySubtitle`.

### 5. Live Preview

A line matching `DEPENDENCY_NAVIGATION_BULLET_RE` (updated for cross-note
links) is replaced in LP by an inline flex row of chips, one per Task Dep
Link, plus `+`. Chip accent follows the target’s current checkbox. Done /
cancelled targets render muted and struck; they remain until the user
removes them, so history is visible and `[dependsOn::]` is not silently
rewritten on complete. Reading view gets the same treatment from a
post-processor, so dash embeds of a project note show chips too.

This is the same “Markdown is the source, the widget is display-only”
contract as freshness marks (`docs/freshness.md`).

### 6. Code surfaces

| Surface | Change |
| --- | --- |
| bob-navigation-hotkeys | Invert `formatDependencyNavigationBulletWithMarker` to one plain-link line with ` • `; extend the link regex to `[[note#^id]]`; vault-wide stage-2 picker; retarget `!`; show Depends on in Task Link mode; write aliases; LP chip decoration + `+` / `×` |
| `~/.config/bob/config.yml` | Keep `name: dependsOn` / `values: local_task_id`; document that this type is vault-wide with same-note rank (only consumer today) |
| block-id-prompt | `isDependencyTransclusionLink` → managed DEPENDS ON bullet (and still refuse leftover transclusion deps until migrated) |
| task-status-cycler | Ctrl+Enter on a Task Dep Link closes the target; keep `recoverBlockedDependents` |
| bob-cli `task-status-hooks` | Promotion graph from `dependsOn` IDs (ADJ-2); repair the managed bullet from the field; stop treating arbitrary sole transclusions as edges; docs + JSON: `dependency` still means “reached via dependsOn,” not “reached via embed” |
| `scripts/migrate-dependency-bullets.mjs` | Invert the formatter: collapse `dependsOn`-matching transclusion children onto one plain-link line; leave unmatched embeds; dry-run default |
| glossary | New `task-dep-link` strand; edit `task-link` |
| tests | navigation hotkeys (format, picker membership, `!`, counted, Task Link mode); hooks fixtures replacing sole-transclusion edges with `dependsOn`; cycler close-from-link; migration dry-run on a fixture that includes a reading-material embed |

Bob Mac Capture stays a thin client; it does not author dependencies today.

### 7. Migration

Scale is friendly: 45 active `dependsOn` field lines, 57 under-task
transclusions, 13 live blocked parents.

1. Dry-run `migrate-dependency-bullets.mjs` (inverted) on `~/bob`.
2. Confirm it rewrites only children whose target id is in `[dependsOn::]`.
3. `--write`, then `bob task-status-hooks --dry-run` and a live run.
4. Leave `DEPENDENCY_TRANSCLUSION_BULLET_RE` in the parser until a later
   cleanup so any missed embed still unlinks through `!`.

### 8. What “done” looks like in the note

Before (`body.md`):

```markdown
- [?] #task Make appt w/ Rahway Hospital for CT scan! [dependsOn:: body__hospital-swarm] ^rahway
	- ![[#^hospital-swarm]]
	- **PHONE NUMBER:** (732) 381-4200
	- 🗓️ **SCHEDULE LOG**
		- *2026-08-06 → 2026-08-10* — Next day that hospitals are open
```

After, source:

```markdown
- [?] #task Make appt w/ Rahway Hospital for CT scan! [dependsOn:: body__hospital-swarm] ^rahway
	- 🔗 **DEPENDS ON:** [[body#^hospital-swarm|Launch swarm to find hospital]]
	- **PHONE NUMBER:** (732) 381-4200
	- 🗓️ **SCHEDULE LOG**
		- *2026-08-06 → 2026-08-10* — Next day that hospitals are open
```

After, Live Preview (schematic): the DEPENDS ON line becomes a chip row
`🔗  [?] Launch swarm to find hospital   +` in Blocked rose, clickable,
with the phone number and Schedule Log still ordinary children.

`sase_dyn_agent_fam.md` “Read dynamic agent family critique!” keeps its two
`![[ref/chat/…#^ref]]` embeds. Those were never Task Dep Links.

## Risks and limits

- **Alias drift.** Task titles change; aliases on the managed bullet go
  stale until the next picker write or hooks repair. Acceptable; the
  `^block-id` is the identity. LP chips should read the live line, not the
  alias.
- **Hooks now rewrite a human-facing line.** Repair must be exact
  (stable order: existing order, then append new ids; do not alphabetize
  and churn git). Unresolvable ids stay in `[dependsOn::]` and warn; they
  are not dropped.
- **Counted `!`.** Today it toggles embeds on N lines. After retargeting,
  counted `!` on sequential `#task` parents should open **one** picker and
  apply the result to each parent (same as counted `Ctrl+Shift+P`). Counted
  `!` on mixed non-task lines keeps falling through to Vim.
- **Cycles.** Tasks already allows them (they stay Blocked). The picker
  excludes self and does not try to be a SAT solver.
- **844 open tasks** in the picker is the same corpus `^^` already scans.
  Same-note rank plus fuzzy filter keeps it usable.
- **Sticky lanes.** Promotion-via-`dependsOn` still raises Ready blockers
  to Next when the parent is linked today. That is current behavior
  (`decisions:task-lanes-are-sticky`, “Dependency-promoted Next is sticky
  too”). Unifying the graph does not change the lane rule.

## Verdict

Take the request. Reverse the 2026-07 “one transclusion per dep”
migration, keep `[dependsOn::]` as the index, put ordinary Task Links on
the managed `🔗 **DEPENDS ON:**` line the parser already knows, and give
that line the vault-wide picker `Ctrl+Shift+P` almost has. Beauty is the
Sub-projects line in source plus status chips in Live Preview — the same
chip system the dash and freshness marks already speak.

## Sources

- `glossary:task-link`, `glossary:work-log`
- `decisions:task-status-is-derived`, `decisions:task-lanes-are-sticky`
- `docs/task-status-hooks.md`, `docs/dataview.md`, `docs/freshness.md`, `docs/projects.md`, `docs/capture.md`
- `plan:202607/blocked_task_status.md`, `plan:202607/dependency_status_propagation.md`, `plan:202607/hide_deterministic_task_fields.md`
- bob-plugins: `plugins/bob-navigation-hotkeys/main.js` (legacy DEPENDS ON grammar, `local_task_id`, `!` toggle, Task Link mode hiding), `plugins/block-id-prompt/main.js` (`^^` picker, `isDependencyTransclusionLink`), `plugins/task-status-cycler/main.js` (Ctrl+Enter on embeds), `scripts/migrate-dependency-bullets.mjs`
- `~/.config/bob/config.yml` `properties.dependsOn`
- Live vault 2026-10-02: `bob query --tasks 'is blocked'` / `filter by function task.dependsOn.length > 0` / `not done`; `body.md`, `cash.md`, `sase_agents_repo.md`, `sase_dyn_agent_fam.md`, `sase.md`
