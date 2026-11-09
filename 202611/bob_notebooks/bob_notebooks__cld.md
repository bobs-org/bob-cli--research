---
title: "Notebooks — a third note kind for Bob"
description: "Research, critique, and a recommended design for a `type: [[notebook]]` note kind: capture grammar, root-parent index, glossary term, and the first vault migration."
researcher: cld
date: 2026-11-09
---

# Notebooks: a third note kind for Bob

> **Bottom line.** Build it. The vault already has a lot of notebooks that just lack a
> type: about 500 untyped root notes, 433 of them stranded under the retired zorg tree.
> Three of them were factored out of area notes by hand in the last six weeks, and
> `meet.md` keeps a hand-written "Related notes" index *with one-line summaries*. A
> notebook type plus a generated index turns that hand labour into a system.
>
> Change one part of the plan. Do **not** use `@@` for notebook notes: `@@route` is
> already the draft-wide default-route declaration, and today `@@foo#x`, `@@foo^id`
> and `@@foo+id` are rejected outright. Instead, let the **destination decide**. On a
> notebook, the existing `@nb`, `@nb#section`, `@nb+id` and `@nb^id` forms write
> notes instead of tasks. `@@nb` keeps working as a declaration, and every typing alias
> works with no new rule except `.`→`^` after `@nb#section`. Create notebooks with
> `@route^id@ %n` as proposed. The item's text becomes the required `summary:`.

---

## Contents

1. [What exists today](#1-what-exists-today)
2. [Critique: is this a good idea?](#2-critique-is-this-a-good-idea)
3. [Requirement adjustments (called out)](#3-requirement-adjustments-called-out)
4. [Recommended design](#4-recommended-design)
5. [Glossary term draft: Notebook](#5-glossary-term-draft-notebook)
6. [Vault survey and the first notebooks](#6-vault-survey-and-the-first-notebooks)
7. [Alternatives considered](#7-alternatives-considered)
8. [Phasing, risks, and open questions](#8-phasing-risks-and-open-questions)
9. [Recommended solution](#9-recommended-solution)

---

## 1. What exists today

### 1.1 Capture grammar facts that shape the design

I checked every finding below against `docs/capture.md`, `docs/reference/capture-syntax.md`,
the parser in `src/native/capture_language/`, and the installed `bob 0.5.0` binary run
against an empty scratch vault.

| Form | Today's meaning | Parse result for the proposed syntax |
| --- | --- | --- |
| `@@route` | **Draft-wide default destination** for otherwise-unrouted items, as tasks (`docs/capture.md` "Global destination declaration"). `@@` is "reserved for this grammar". | `Idea @@foo` → mode `task`, route `foo` |
| `@@foo#x`, `@@foo^id`, `@@foo+id` | **Explicit errors**, "rather than literal task text" (`parse_global_destination_token`, `capture_language/draft.rs:2516`). | `invalid_global_destination: @@ takes a route` |
| `@route#Section` | Ordinary bullet (`- text [created::DATE]`) into a matching non-`Tasks` heading. Matching is prefix, then slug. **If nothing matches, the bullet falls back to the zeroth (pre-heading) section.** | `Idea @foo#bar` → mode `bullet` |
| `@route+id` | Child bullet under an existing **task**. Non-task block IDs are rejected. | `Idea @foo+baz` → mode `sub_bullet` |
| `@route^id` | New open **task** with that block ID. | mode `task`, block_id set |
| `@route^id@` | Create the project note `<route>_<id>.md` (Project Note Capture). | mode `project_note` |
| `%n` | **Pomodoro note**: a plain bullet on today's current Pomodoro. Refused with any `@route`, `s:`, or `$`. | `@work^x@ %n` → `pomodoro_note_conflict` |
| Aliases | `.` after a space → `@`; `.` right after `@route` → `^`; `,` → `+`; `/` or `\` → `#` wherever completion would open a `#` menu. `/` stays literal inside `@@` routes. | lexical (`capture-rewrite` never opens the vault) |

Relevant precedents:

- **Destination-aware parsing already exists.** `capture-parse` loads a memoized
  *record policy* (`src/native/capture_parse.rs:120`). It warns `record_collection_route`
  when `Title @eat` targets a record collection and offers the `@eat/` rewrite. A
  "notebook policy" can follow the same pattern: a lexical preflight, then one
  frontmatter read per `@route`.
- **Project notes treat H2 sections as drawers.** On a project's `^prj` task, the note's
  `##` sections act as drawers: matched exactly and created on demand in Title Case. A
  notebook section is the same idea.
- **A block-ID suggester exists in both clients.** bob returns up to three deterministic
  `block_id_suggestions` (e.g. `Fix flaky gkeep test` → `fix-flaky-gkeep`). Mac
  Capture's Block ID composer shows them "press Tab for suggestions"
  (`CapturePickerPresentation.swift:944`). The Obsidian block-id-prompt goes further: it
  opens with a *selected* suggestion that Enter accepts (bob-plugins
  `docs/block-id-defaults.md`). That is the UX the request asks for.
- **Side finding (doc bug).** `docs/capture.md:8327` says "a `%n` after the seal opens
  Pomodoro-name completion". The binary actually opens that completion for a **`#`**
  after the seal; `%n` there yields `pomodoro_note_conflict`. This looks like a stale
  remnant of the `#`→`%n` rename, and it sits exactly where the new notebook meaning of
  `%n` would land.

### 1.2 Note kinds in bob-cli

- `NoteKind { Area, Project, Other }` (`src/native/pomodoro_homes/facts.rs:49`) drives
  root-parent walks. An `Other` note is walked *through*, so a notebook would already be
  transparent to root attribution without code changes.
- `CaptureTargetKind { Inbox, Area, Project, Record }`
  (`src/native/capture_targets.rs:233`) is the `@` route catalog. Mac Capture decodes
  `kind` as a **string** and falls back to a `doc` icon
  (`CapturePickerView.swift:1087`), and decodes `mode` as an optional string
  (`CaptureModels.swift:120`). A new `notebook` kind and new modes are therefore
  **additive and safe** for older app builds.
- **Trap:** `parent_notes::parent_candidates` reuses the capture-target set for
  task-owning flows: `bob ref create -P`, ref jobs, `URL @route`, `gkeep pull`, and
  births. It filters out `Record` today. It must also filter out `Notebook`, because a
  notebook can never hold a reading task. Every consumer of the capture-target set needs
  that review; the safe default is to exclude notebooks.
- `bob task move` already **repairs inbound links vault-wide**: wikilinks, embeds,
  aliases, block links, and pathless links (`docs/task-move.md` §"links"). Any gesture
  that moves note bullets between files, such as extracting a section into a notebook,
  should reuse that engine.

### 1.3 Rendering precedents

| Precedent | Who writes | Who renders | Lesson |
| --- | --- | --- | --- |
| `🧩 **Sub-projects:** [[a]] • ~~[[b]]~~ ✅` under `^prj` | `bob projects sync` (machine-owned line) | plain Markdown, plus plugin link chips | Machine-owned child indexes are an established Bob pattern |
| `## Tasks` status badge row | `bob task reconcile` | plain Markdown | Generated rows can sit inside user notes |
| `bob-period-parts` / `bob-stats-strip` fences | bob writes the fence once | bob-ledger-tools renders live from bob JSON | "**No number is ever written into Markdown**" (`docs/periods.md`) |
| `[!agent]`, `[!mail]` callouts | bob / bob-mail | custom CSS in `bob-ledger-tools/styles.css:7200` and `bob-mail/styles.css` | Custom callout types are the house way to make a block beautiful |

### 1.4 What the vault says (evidence for the feature)

I scanned all 5,548 Markdown files in `~/bob` (excluding `done/`, `.obsidian/`, and the
gitignored `lit_review/` and `xlib/`):

- **About 500 untyped root notes, excluding daily and monthly notes.** Only 20 have no
  `parent` at all, and those are mostly junk: eight empty `Untitled*.md` files, an empty
  file named `.md`, agent instruction files (`CLAUDE.md`, `GEMINI.md`, and others),
  `obsidian_vimrc.md` (a config file), and two 2022 zorg exports.
- The real orphan problem is **433 untyped notes whose `parent` chain never reaches an
  area or project**. Each chain ends at `org.md`, the root of the migrated zorg tree
  (`org > horizon > h2_role > work|own|mind`, `org > z_key > who`,
  `org > projects > zorg`, and so on). Another **67 untyped notes already have a parent
  chain that reaches an area or project**; they are notebooks in everything but name
  (`dev_ideas`, `gtd_ideas`, `linux`, `taxes`, `dog`, `vet_log`, …).
- **Bryan is already building notebooks by hand.** He extracted `legacy_gkeep_notes`
  from `gkeep_inbox` (2026-09-28), `legacy_job` from `job` (2026-10-12), and
  `legacy_dad` from `dad`/`abby` (2026-11-02). He created `haircut.md` under `body` and
  `tv.md` under `fun` with `_templates/new_note.md`, which stamps only `parent` and
  `created`, so every such note is born untyped.
- **Hand-maintained indexes are rotting.** Several area notes carry "Related notes:"
  lists. `meet.md` even writes summaries: `[[the_monthly]] | The Monthly Meeting w/
  %thazel Reports`. That is the requested feature, done by hand and kept current by
  nobody. `dev.md`'s list mixes notebooks, a project, and an area.
- **Large H2 sections are waiting to be factored out.** The biggest non-`Tasks` H2s in
  area notes are all `## Legacy Notes`: `gtd` 44 lines, `dev` 31, `fun` 29, `cash` 25,
  `body` 19. **137 inbound block links** from other files point at their 35 block IDs,
  so extracting them without link repair would break those links.

---

## 2. Critique: is this a good idea?

**Yes. It is the missing piece between "a heading in an area note" and "a whole new
area or project."**

What it fixes:

1. **Knowledge with no obligations.** Today the only first-class homes are areas and
   projects, and both carry task machinery: Ready caps, `## Tasks` grouping, Stats
   roots, off-clock defaults, and `]s` review. A notebook explicitly opts out. It holds
   notes, is never a Stats root, and is never part of review. That separation is the
   value; it should not be watered down by allowing tasks in.
2. **Discoverability.** A generated index in the owning area or project replaces the
   rotting "Related notes" lists.
3. **A landing zone for the zorg backlog.** Hundreds of legacy notes become reachable by
   retyping and re-parenting them, with no content rewrites and no renames.
4. **Smaller task notes.** Moving `## Legacy Notes` and similar sections out of `dev.md`
   and `gtd.md` keeps area notes about current work.

Where the original plan goes wrong or is underspecified:

| # | Concern | Severity |
| --- | --- | --- |
| C1 | `@@foo` collides with the existing global-destination declaration. Overloading it would give one token two scopes: draft-wide for areas, item-local for notebooks. Every `@@foo#…` / `^…` / `+…` form is a deliberate error today. | **High**: breaks a recorded grammar rule (`decisions:capture-sigils-say-where-what-how` lists `@@note` as a draft-wide route) |
| C2 | Under the original plan, what `text @notebook` should do (single `@`) is undefined. It would either write a task into a notebook, violating the invariant, or be refused, which is pure friction. Either way `@@` becomes redundant. | High |
| C3 | `@route#Section` silently falls back to the zeroth section when no heading matches. For notebooks that is a misfile. Sections should be created on demand, with drawer-style exact matching. | Medium |
| C4 | "Only note bullets" needs a split between hard and soft rules. Legacy notes contain preamble paragraphs, `====` dividers, and in `quote.md`, callouts with block IDs. Refusing those would block migration. | Medium |
| C5 | Rendering only in the root parent hides a leaf project's notebooks when Bryan is in that project. | Low–medium |
| C6 | "Factor an H2 out" is described as later work, but Bryan already does it by hand, and doing it without link repair breaks links (137 inbound block links in the Legacy Notes sections alone). | Medium |
| C7 | A required summary must not make readers brittle. Old or hand-made notebooks will lack one. | Low |

---

## 3. Requirement adjustments (called out)

Each adjustment is numbered so the lead can accept or reject it piecemeal.

- **A1 — Destination decides; no new `@@` forms.** On a notebook, the existing
  item-local forms write notes: `@nb` (top-level note), `@nb#sec` (note in an H2
  section), `@nb+id` (sub-bullet under note `^id`), `@nb^id` (note with that ID).
  `@@nb` keeps its meaning, a draft-wide default destination, and on a notebook every
  unrouted item becomes a note. So the literal `text @@foo` from the request still works
  for a single item. `@@nb#…`, `@@nb+…` and `@@nb^…` stay refused, with a teaching
  rewrite to the item-local form, because a block ID cannot be draft-wide.
- **A2 — Notebook sections use drawer rules.** `#sec` must match an existing H2 by
  slug. A strict-prefix or edit-distance-1 near miss is refused. A new section is
  created on demand in Title Case, and `#"Exact Title"` forces creation. There is no
  zeroth-section fallback. Area and project notes keep today's section-bullet behaviour.
- **A3 — Add `@route#sec^id`.** One small grammar addition: a section bullet with a
  block ID (`Tiramisu @recipes#desserts^tiramisu`). Make it valid for every route, not
  only notebooks, so `capture-rewrite` stays lexical and the `.`→`^` alias can fire after
  `#sec`.
- **A4 — Hard and soft body rules.** **Hard:** no `#task` lines anywhere in a notebook
  (capture refuses, `bob notebooks check` errors). **Soft (lint warning):** top-level
  content should be `- ` bullets under an optional H1 and `## ` sections. Nested content
  inside a bullet (code, images, quotes, sub-bullets) is unrestricted.
- **A5 — `summary:` is required at creation and tolerated on read.** Capture, the
  create command, and extraction all require it. The index shows an "add summary" chip
  when it is missing. Keep it to one line, about 120 characters or fewer, plain text.
- **A6 — One index rule for every owner.** Each area or project note indexes the
  notebooks in its subtree, stopping at the next root parent. For a root parent this is
  exactly the requested rollup through non-root children (sub-projects and nested
  notebooks). For a leaf project it is that project's own notebooks. Sub-areas, being
  roots, keep their own indexes. An optional one-line hint ("More in sub-areas:
  [[fun]] · [[kelly]]") keeps them discoverable from the parent.
- **A7 — No numbers in Markdown.** bob writes only stable facts: links, titles,
  summaries, and nesting. Note counts, section counts, and "updated 2d ago" are rendered
  live by bob-ledger-tools. This follows the period-notes rule and avoids churning
  `dev.md` on every capture.
- **A8 — Creation is the `^` seal plus `%n` only.** `@route^id@ %n` creates a notebook.
  The `:` seal (offer form) and a `#pomodoro` after the seal are refused for notebooks,
  since there are no tasks to link or offer.
- **A9 — Promote extraction to a first-class gesture.** Add `bob notebooks extract`, an
  Obsidian command, and a capture move-in bullet. All three reuse the task-move link
  repair engine. Ship it after the core, but design for it now (C6).
- **A10 — Migration never renames files.** It edits frontmatter (`type`, `parent`,
  `summary`) and makes light body normalizations. Legacy `^z-…` block IDs stay. Zorg
  todo and tickler notes are *not* notebooks (§6.4).
- **A11 — `URL @notebook` becomes a bookmark note, not a reference job.** A notebook
  cannot own the reading task a reference job creates, and a notebook user typing a URL
  means "save this link here". `URL @owner` remains the reading-queue route.

---

## 4. Recommended design

### 4.1 Definition and invariants

```yaml
---
parent: "[[dev]]"                 # required: an area, project, or notebook
type: "[[notebook]]"              # the new kind; bare [[notebook]] also accepted
summary: Linux setup, admin commands, and machine gotchas.   # required, one line
created: 2026-11-09T09:14:00-05:00
template: "[[new_notebook]]"      # same convention as new_project
---
# Linux

- A top-level note [created::2026-11-09]
	- nested detail is free-form (code, images, sub-bullets)
- A named note [created::2026-11-09] ^kernel-params

## Commands

- `journalctl -u bob-vault-sync --since today` [created::2026-11-09]
```

| Rule | Kind | Enforced by |
| --- | --- | --- |
| `type: "[[notebook]]"`; `notebook.md` type note exists with `parent: "[[type]]"` | definition | vault convention, matching `area.md` and `project.md` |
| `parent` resolves to an area, project, or notebook; no cycles | hard | `bob notebooks check` (error); capture and create refuse |
| No `#task` line anywhere in the body | hard | capture refuses; Ctrl+Shift+M / `bob task move` refuse notebook destinations; `check` errors |
| No area, project, or reference note has a notebook as `parent` | hard | `check` errors (a notebook must never become a task's residence by proxy) |
| `summary` present, one line, ≤ ~120 characters | soft | creation requires it; `check` warns; the index shows a chip |
| Body is an optional H1, top-level `- ` bullets, and `## ` sections | soft | `check` warns (paragraphs, `====`, H3+, top-level callouts) |
| Block IDs unique within the note | hard | capture and the ID writer refuse duplicates |
| Never a root parent, Pomodoro home, Stats root, Ready lane, or review item | derived | `NoteKind::Other` is already transparent in root walks |

Tree terms used below:

- **Owner(nb):** the nearest area or project on nb's parent walk, walking through notebooks.
- **Root(nb):** the root parent of Owner(nb), using the existing rule (an area at any
  depth, a `root: true` project, or the outermost project).
- **Title(nb):** the first H1, or else the humanized stem (`bugyi_dog_policy` → "Bugyi Dog Policy").

### 4.2 Capture grammar on a notebook route

**One rule: the destination's kind decides what a route form writes.** On an area or
project, `@x` writes a task. On a notebook, it writes a note. No new sigil is added,
consistent with `decisions:capture-sigils-say-where-what-how` ("`@` says where").

| Draft | Writes | Notes |
| --- | --- | --- |
| `Idea text @nb` / `@nb Idea text` | `- Idea text [created::DATE]` appended to the zeroth section (after the last top-level bullet before the first `## `) | append = chronological, matching section bullets |
| `Idea text @nb#sec` | same, appended to `## Sec` | drawer matching: exact slug, near-miss refused, missing section created in Title Case at the end; `#"Exact"` forces creation |
| `Idea text @nb^some-id` | `- Idea text [created::DATE] ^some-id` in the zeroth section | ID unique in the note |
| `Idea text @nb#sec^some-id` | same, in `## Sec` | adjustment A3 |
| `Detail @nb+baz` | `\t- Detail` appended as the last child of the bullet carrying `^baz` | no `created` stamp, matching existing `+id` children; any bullet depth |
| `@nb+baz` + bullets | each first-level bullet becomes its own child note under `^baz` | mirrors `decisions:capture-bullets-mirror-the-task-block` |
| `@nb#sec` alone + bullets | section list: each bullet becomes a note in `## Sec`; `- text ^id` names it | existing section-list grammar |
| `text @@nb` (any position) | every otherwise-unrouted item in the draft becomes a top-level note in nb | existing declaration semantics, now destination-aware |
| `URL @nb` | `- <title or URL> [created::DATE]` bookmark note | adjustment A11; `URL @owner` still queues a reference |
| `text %c @nb` | note with clipboard lines as children | `%c` composes as today |
| `text @nb %n` | accepted; `%n` is redundant ("as a note") | friendlier than refusing |

**Refusals on a notebook route.** Each teaches, with a rewrite to the owner route where
one exists (`@dev_ideas` → `@dev`):

| Marker | Message shape |
| --- | --- |
| `s:<N>`, `$<N>`, free `#type` | "`dev_ideas.md` is a notebook — notes take no schedule/priority/type. Capture the task in its home with `@dev`." |
| `@nb:id`, `=…`/`x…` link suffixes, `@nb+id!` | "notebooks hold notes, not Pomodoro-linked tasks — write `@dev:id`." |
| `&`, `*`, `~`, `~~` | "dependencies and relations link tasks; a notebook note isn't one." |
| `@a+x > @nb` (transfer), lone `@nb` (pull) | "a notebook holds no tasks to move in or pull." |
| `@@nb#sec`, `@@nb+id`, `@@nb^id` | "`@@` declares a draft-wide route; put `#sec` / `+id` / `^id` on the item: `@nb#sec`." |

**Creating a notebook.**

| Draft | Result |
| --- | --- |
| `@dev^nvim@ %n Neovim config notes, plugin picks, and gotchas` | `dev_nvim.md` with `parent: "[[dev]]"`, `type: "[[notebook]]"`, `summary: Neovim config notes, plugin picks, and gotchas`, `created`, `template`, and `# Nvim`. The owner's root index is updated **in the same all-or-nothing batch**. |
| …plus `- First note` bullets | each first-level bullet becomes a top-level note |
| …plus `- PLUGINS` with nested bullets (or `- #plugins`) | an ALL-CAPS bullet with nested notes becomes `## Plugins` with those notes, mirroring project-note drawers |
| …plus `- ^blight` (phase 3) | **moves** the owner note's bullet `^blight` into the new notebook, repairing links; parallels `- ^id` task moves in project capture |
| …plus a childless `- #legacy-notes` (phase 3) | **moves** the owner's whole `## Legacy Notes` section in. Today a childless `- #x` is an incomplete form (`drawer_notes`), so this meaning is free. |
| `@dev_nvim^lua@ %n …` | nested notebook `dev_nvim_lua.md` under `dev_nvim` |
| `@dev:nvim@ %n`, `@dev^nvim@#bugs %n` | refused (A8) |
| `@dev^nvim@ %n` with no text | refused: "a notebook needs a one-line summary — type it as the item text" |

Naming follows project capture: `<route>_<id>.md` with `-` mapped to `_`. That keeps
routes namespaced and sorted next to their owner in file lists. Existing notebooks keep
their stems (A10).

**Typing aliases.** All of these are lexical, so they work without vault access:

| Typed | Becomes | Rule |
| --- | --- | --- |
| `Idea .` | `Idea @` | existing: `.` after a space following text |
| `Idea @dev_ideas.` | `Idea @dev_ideas^` (opens the ID composer) | existing: `.` right after `@route` |
| `Idea @dev_ideas/` | `Idea @dev_ideas#` (section menu) | existing: `/` where a `#` menu opens |
| `Idea @dev_ideas#plugins.` | `Idea @dev_ideas#plugins^` | **new**: extend `.`→`^` to right after `@route#section` (pairs with A3) |
| `Idea @dev_ideas,` | `Idea @dev_ideas+` (note-parent picker) | existing: `,` where the parent picker opens |
| `@dev^nvim.` … | (seal typed as `@`, so no alias needed) | unchanged |

`;`→`:` will still fire lexically after `@nb`. The resulting `@nb:` is then refused at
parse time with the teaching message above, which is acceptable.

**Completion, preview, and IDs.** bob stays the only grammar authority
(`decisions:mac-capture-is-a-thin-client`).

- `capture-targets`: new `kind: "notebook"` rows carrying `owner`, `root`, `summary`,
  and a breadcrumb label (`dev › Linux › Athena`). Sorted after projects. **Excluded
  from `parent_candidates`** and from every task-destination picker (inbox routing,
  Ctrl+Shift+M, Gmail route labels).
- `capture-parse`: a memoized notebook policy (lexical preflight, then a frontmatter read
  per `@route`, the same shape as the record policy). It reports modes `notebook_note`,
  `notebook_sub_note`, and `notebook_create`, reusing `route`, `section`, and
  `block_id`.
- `capture-complete`:
  - `@nb#` lists sections with drawer-style creation rows.
  - `@nb+` lists note bullets: ID'd ones first, ID-less ones with
    `requires_block_id: true` and suggestions.
  - `@nb^` returns `block_id_suggestions` derived from the item text, with the first
    marked `default: true`.
  - Mac Capture's composer **pre-selects** that default, so Return accepts it and typing
    replaces it. This matches Obsidian's block-id-defaults UX: collision-aware `stem-2`,
    32-character cap.
- `capture-task-id`: extend it (or add a sibling such as `capture-block-id`) so it can
  name an ID-less *note* bullet in a notebook. Picking one in the `+` picker then
  becomes `@nb+<id>`.
- Dry-run preview copy, e.g. `✓ captured  linux.md  📓 Linux › Commands`, with the
  bullet echoed. Notebook creation previews `📓 New notebook dev_nvim.md · in [[dev]]`.

### 4.3 The Notebooks index

**Scope (A6).** Note *X*, an area or project, lists every notebook whose Owner lies in
X's subtree, stopping at descendants that are roots themselves:

- For a root parent this is the full rollup: its own notebooks, nested notebooks, and
  one group per non-root sub-project.
- For a leaf project it is its own subtree.
- Notebooks never get an index; their children are already a click away in the parent's
  index and in Obsidian's backlinks.

**Ownership.** The `## Notebooks` section's *content* is machine-owned and rewritten
canonically. Its *position* belongs to Bryan: on the first write bob inserts it right
before `## Tasks`, or at the end when there is none, and afterwards rewrites it wherever
it sits. bob deletes the section when the subtree has no notebooks. Capture never
targets it: it joins the status-group headings as a non-target for `@x#`.

**Bytes bob writes.** Stable facts only (A7):

```markdown
## Notebooks

> [!notebooks]
> - **[[dev_ideas|Dev Ideas]]** — Open ideas and proposals for personal dev tooling.
> - **[[linux|Linux]]** — Linux setup, admin commands, and machine gotchas.
>     - **[[athena|Athena]]** — Upkeep, update, and recovery notes for the athena home server.
> - **[[mac|Mac]]** — macOS Q&A, tools, and new-laptop setup notes.
> - **[[networking|Networking]]** — Networking and fediverse/ActivityPub notes.
```

A root with sub-project groups (e.g. `sase.md`) adds one sub-header per descendant
project. Closed projects use the Sub-projects line's decorations:

```markdown
> - **[[sase_ideas|SASE Ideas]]** — SASE ideas and proposals captured in zorg, Oct 2025 – Feb 2026.
>
> 🧩 **[[sase_memory]]**
> - **[[sase_memory_design_notes|Design Notes]]** — …
>
> 🧩 ~~[[sase_blog]]~~ ✅
> - **[[sase_blog_0_legacy_notes|Legacy Notes]]** — …
```

Ordering is alphabetical by title within each level, so it stays stable. Groups follow
tree order: the root's own notebooks first, then each sub-project in Sub-projects order.

**Why a callout under an H2.**

- The H2 gives an outline entry, a `#Notebooks` anchor, native folding, and a clear
  capture boundary.
- The callout gives a stable DOM hook: `.callout[data-callout="notebooks"]`. That allows
  **CSS-only beauty** in both Reading view and Live Preview, where callouts render as
  widgets and post-processors run.
- Every link is a **real wikilink**, so graph view, backlinks, unresolved-link checks,
  agents, and `git diff` all see the structure.
- Without the plugin, it degrades to a default callout with a bullet list.

**Rendering layers (bob-ledger-tools).**

1. **CSS only** (always on):
   - A soft card with a notebook icon (`--callout-icon: lucide-notebook-tabs`) and a calm
     accent colour.
   - The callout title is hidden because the H2 already names the block.
   - Rows show the title in semibold and an em dash, with the summary in
     `--text-muted`.
   - Nested rows hang from a thin tree rule.
   - Sub-project headers reuse the Sub-projects colours.
2. **Live chips** (post-processor, data from `bob notebooks list -f json`, cached and
   refreshed on vault events):
   - Right-aligned, tabular-numeral chips such as `48 notes · 3 §` and `updated 2d`.
   - An amber `add summary` chip that opens the notebook's properties.
   - A subtle `↻` chip when the live `summary:` differs from the written text. The row
     shows the live text; bob rewrites it at the next sync.
3. **In each notebook** (plugin-only, never written): a breadcrumb in the note header,
   e.g. `📓 dev › Linux › Athena`.

### 4.4 Commands and gestures

**bob-cli: `bob notebooks`**, under the help's *Vault* section next to `records` and
`periods`. Membership rule: "commands that read or write notebook notes". A bare
`bob notebooks` runs `list`.

| Command | Purpose |
| --- | --- |
| `bob notebooks list [-r ROOT] [-f human\|json]` | Read-only tree per root: title, summary, counts, last update, lint. The JSON feeds the plugin chips. |
| `bob notebooks check [-f …]` | Read-only lint over the hard and soft rules (§4.1); exits 1 on errors. |
| `bob notebooks sync [-d] [-r ROOT]` | Writes or refreshes every `## Notebooks` index and deletes empty ones. Runs in `bob nightly` after `task archive`, and in the same batch as any capture or command that creates or moves a notebook. |
| `bob notebooks create PARENT ID -s SUMMARY [-t TITLE] [-d]` | The engine behind `@route^id@ %n` and the Obsidian command. |
| `bob notebooks extract NOTE SECTION [-i ID] [-s SUMMARY] [-d]` | Moves an H2's notes into a new child notebook, **repairing inbound block links vault-wide** with the task-move engine, and drops the emptied heading. Phase 3. |

Following `cli_rules.md`, every long option gets a short alias, options are alphabetical,
and output is coloured.

**bob-plugins:**

- **Create notebook here.** Run from an area, project, or notebook. Prompts for title
  and summary; the ID is pre-filled from the title via block-id-defaults logic.
- **Extract section to notebook.** Cursor in an H2; calls `bob notebooks extract`.
- **Move note to notebook.** Ctrl+Shift+M on a non-task bullet picks a notebook and
  section; same link repair. Phase 3.
- **Guards.** Task pickers (Ctrl+Shift+M for tasks, inbox routing) never list notebooks.
- **CSS and post-processor** for `[!notebooks]` (§4.3).

**Bob Mac Capture:**

- `book.closed` icon for `kind == "notebook"`.
- Notebook preview copy.
- Composer default-suggestion pre-select.
- Mode labels for the three new modes.

Every Mac change is additive, gated by macOS CI.

**Vault:**

- `notebook.md` type note (parent `[[type]]`) that embeds a `notebooks.base` table of
  all notebooks (parent, summary, created). This is cheap and complements the indexes.
- `_templates/new_notebook.md`.
- Optional: point `new_note` at notebooks (open question Q5).

### 4.5 Cross-cutting impact checklist

| Surface | Change |
| --- | --- |
| `projects/scan.rs` | `frontmatter_is_notebook` beside `frontmatter_is_area/project` |
| `pomodoro_homes/facts.rs` | none required (`Other` is transparent); optionally a `Notebook` variant for clarity, still transparent |
| `capture_targets.rs` | `CaptureTargetKind::Notebook`; JSON `kind: "notebook"` + `owner`, `root`, `summary` |
| `parent_notes.rs` | exclude `Notebook` from `parent_candidates` (refs, gkeep, births, ref jobs) |
| capture planner (`src/native/capture/`) | destination-kind dispatch; notebook sections (drawer matcher); note-parent `+id`; `#sec^id`; refusals; `@@` inheritance; creation; in-batch index update |
| `capture_language/` | `@route#sec^id` token; `.`→`^` after `#sec` in `capture-rewrite` |
| `capture_parse.rs`, `capture_complete.rs` | notebook policy, modes, completion rows, default ID suggestion |
| task move / inbox route / gmail labels | refuse notebook destinations |
| `bob nightly` | `bob notebooks sync` step |
| docs | new `docs/notebooks.md`; `capture.md` + `capture-syntax.md` rows; `projects.md` cross-link; fix line 8327 |
| memory | glossary `notebook` (§5); touch `capture`, `project-note-capture`, `root-parent`; a decision record, "Notebooks hold notes; the destination decides" |
| bob-plugins | CSS + chips + three commands + picker guards |
| bob-mac-capture | icon, copy, modes, composer default |

---

## 5. Glossary term draft: Notebook

> Written to match existing glossary strands. Per house rules it lands through
> `/sase_memory_write`, not by editing files directly.

**Notebook** *(aka notebook note)*

A Bob vault Markdown file with frontmatter `type: "[[notebook]]"` that groups related
notes under an [[area-note]], a [[project-note]], or another notebook, without the
obligations of a new area or project.

- **Body.** Note bullets only: top-level `- ` bullets, each optionally stamped
  `[created::]`, named with a `^id`, and nested with free-form detail. They may be
  grouped under `## ` sections below an optional H1 title.
- **No tasks, ever.** It never holds a `#task` line, so it is never a task's residence,
  a Pomodoro home, a Ready lane, a review item, or a [[root-parent]]. Root walks pass
  through it to its owner, the nearest area or project above it.
- **Frontmatter.** `parent` must resolve to an area, project, or notebook. The required
  one-line `summary:` describes it in the generated **Notebooks** index that
  `bob notebooks sync` maintains in each area or project note above it, down to the next
  root parent. That index's content is machine-owned; its position is Bryan's.
- **Capture.** Capture writes into a notebook through the ordinary route forms, which
  become note forms on a notebook:
  - `@nb` — a top-level note
  - `@nb#section` — a note in that `##` section, created on demand with drawer matching
  - `@nb^id` / `@nb#section^id` — a named note
  - `@nb+id` — a child of the note bullet `^id`
  - `@@nb` — the draft-wide declaration, now writing notes
  - Task-only markers (`s:`, `$`, `#type`, `:id`, `&`, `*`, `~`) are refused, with a
    rewrite to the owner's route.
- **Creation.** `@route^id@ %n <summary>` creates `<route>_<id>.md` (a [[project-note-capture]] seal plus
  the `%n` directive). `bob notebooks extract` factors an H2 section out into a child
  notebook and repairs inbound links.
- **Not** a [[reference-note]], a record note, a [[task-drawer]], a [[period-note]],
  the Pomodoro note `%n` writes on a daily note, or an Obsidian folder.
  See `docs/notebooks.md`.

---

## 6. Vault survey and the first notebooks

### 6.1 Method

1. Parsed the frontmatter of every vault Markdown file outside `done/`, `.obsidian/`,
   `_templates/`, and the gitignored directories.
2. Classified each root note by `type`.
3. Walked each untyped note's `parent` chain until it hit an area or project (filed) or
   ran out (unfiled).
4. Joined post-migration git history from 2026-06-03 on (edit count and last edit) to
   separate living notes from frozen migration output.
5. Sampled content and counted format hazards: zorg `o` todo lines, `- [ ]` tasks,
   `====` dividers, top-level paragraphs.

### 6.2 Where the stranded notes are (unfiled, chain ends at `org`)

| Legacy hub | Notes | Lines | Verdict |
| --- | --- | --- | --- |
| `h2_role > work` (Google era) | 128 | 6,939 | Mostly historical. Mine selectively for dev-relevant knowledge: `sase_ideas`, `vim`, `nvim_plugins`, `best_practice`. |
| `projects > zorg` | 52 | 2,382 | Retired system. Archive, not notebooks. |
| `z_key > who` (1:1 meeting notes, people) | 25 | 2,125 | Tier 2: a "Google 1:1s" notebook under `job`. These hold accomplishment stories for the job search. |
| `type > ref` (old reading lists) | 16 | 1,115 | Superseded by `bob ref`. Skip. |
| `h2_role > own` | 8 | 481 | `mac` (tier 1). `grand_sanitation` and `home_ticks` need a `home` home (Q1). |
| `h2_role > mind` | 11 | 447 | `quote` (tier 2, needs a parent: Q1); `lit_notes` subtree. |
| `tick` / `ticktock` (ticklers) | ~48 | ~380 | Recurring reminders, not notes. Skip. |
| `horizon > now/soon/wait`, `prj` | ~16 | ~700 | Zorg todo lists. Task triage, not notebooks. |
| `maybe` | 12 | ~550 | Superseded by `eat/` records, show/movie records, and the reading queue. Skip. |

### 6.3 Tier 1 — migrate with this change

**18 notebooks across 8 roots.** Together they exercise nesting (`linux › athena`,
`dog › vet_log/…`), a project root (`sase`), re-homing from the zorg tree (`mac`,
`sase_ideas`), and replacing a hand-written index (`meet`). Summaries are drafts for
Bryan to edit. Personal or financial notes are retyped only; their bodies are not
touched beyond the preamble.

| Notebook | Today | New `parent` | Draft `summary` | Body work |
| --- | --- | --- | --- | --- |
| `sase_ideas` | untyped, under `work_ideas` (**unfiled**) | `[[sase]]` | SASE ideas and proposals captured in zorg, Oct 2025 – Feb 2026. | preamble line → summary |
| `mac` | untyped, under `own` (**unfiled**; edited Jul 2026) | `[[dev]]` | macOS Q&A, tools, and new-laptop setup notes. | preamble → summary; `Related: [[linux]]` becomes a see-also bullet; keep `## Legacy Notes` |
| `dev_ideas` | untyped, under `dev` | `[[dev]]` | Open ideas and proposals for personal dev tooling. | preamble → summary |
| `linux` | untyped, under `dev` | `[[dev]]` | Linux setup, admin commands, and machine gotchas. | "Related notes" list → index (children) + see-also bullet |
| `athena` | untyped, under `linux` | `[[linux]]` | Upkeep, update, and recovery notes for the athena home server. | none |
| `networking` | untyped, under `dev` | `[[dev]]` | Networking and fediverse/ActivityPub notes. | preamble → summary |
| `gtd_ideas` | untyped, under `gtd` (edited Nov 2) | `[[gtd]]` | Open ideas and proposals for improving my GTD system. | preamble → summary |
| `taxes` | untyped, under `cash` | `[[cash]]` | Where tax documents live, plus per-year filing notes. | already per-year H2s |
| `dog` | untyped, under `love` | `[[love]]` | Our dogs: vet, care, and pet-cost policy notes. | "Related notes" → generated index |
| `vet_log` | untyped, under `dog` | `[[dog]]` | Dated log of vet visits. | six `====` date lines → `## YYYY-MM-DD` |
| `bugyi_dog_policy` | untyped, under `dog` | `[[dog]]` | Our self-insurance protocol for deciding on costly vet care. | none |
| `rocky` | untyped, under `dog` | `[[dog]]` | Notes on Rocky, including what helped his eyes. | none |
| `lenard` | untyped, under `dog` | `[[dog]]` | Notes on Lenard: arrival, costs, and early vet visits. | none |
| `word_of_day` | untyped, under `love` | `[[love]]` | Kelly's and my "word of the day" list, with definitions. | preamble → summary |
| `kellys_salary_info` | untyped, under `kelly` | `[[kelly]]` | Reference numbers for Kelly's pay and benefits; verify yearly. | none |
| `the_monthly` | untyped, under `meet` | `[[meet]]` | Monthly meeting reports with my Google manager. | three legacy `o` todos → triage into `meet` or archive |
| `all_hands` | untyped, under `meet` | `[[meet]]` | Department all-hands notes from 2025. | none |
| `legacy_dad` | untyped, under `abby` | `[[abby]]` | Legacy zorg notes on being Abby's dad, moved here 2026-11-02. | one `====` line → H2 |

**After retyping:**

- Run `bob notebooks sync` so `dev`, `sase`, `gtd`, `cash`, `love`, `kelly`, `meet`, and
  `abby` gain Notebooks indexes.
- In `meet.md`, drop the `[[the_monthly]]` and `[[all_hands]]` entries from the
  hand-written list. Keep `[[recur_meet]]`, which holds recurring-meeting todos and is
  not a notebook.
- Repoint the `abby.md` line "(see [[legacy_dad]] …)" to the index, or leave it.

### 6.4 Tier 2 and Tier 3, and what is *not* a notebook

- **Tier 2** (retype or re-home once Bryan answers Q1/Q2):
  - `quote` — curated `> [!quote]` callouts, so it carries the soft-rule warning.
  - `grand_sanitation` (+ a `home` area?).
  - `vim`, `nvim_plugins`, `this_week_in_nvim`, and `best_practice` → `dev`.
  - The `ai_ref` subtree (`agent_ref` at 707 lines, `claude_code_ref`, `xprompt_ref`,
    `langgraph_ref`, via `dev_ref`) → `dev` as nested notebooks.
  - `interview_notes`, `legacy_job`, and a Google 1:1s notebook → `job`.
  - `haircut` and `outlive` → `body`. `outlive` has one `- [ ]` line to move out first.
  - `legacy_gkeep_notes` → `gkeep_inbox`.
  - `sase_blog_0_legacy_notes` → `sase_blog`.
- **Tier 3** (dogfood `bob notebooks extract` once link repair ships): factor
  `## Legacy Notes` out of `gtd`, `dev`, `fun`, `cash`, and `body` into
  `legacy_<area>` notebooks. That name matches Bryan's own `legacy_dad` and
  `legacy_job`; Q2 asks whether to keep it. This must repair the **137 inbound block
  links** found in §1.4.
- **Not notebooks:**
  - zorg-system notes (`zorg_*`)
  - tickler files (`tick_*`, `home_ticks`, `body_ticks`) and zorg todo lists
    (`now_*`, `soon_*`, `wait_*`, `now_sase`, `recur_meet`) — tasks and recurrences,
    which belong in task triage
  - `pomodoro.md` (rollover Pomodoros)
  - dashboards (`dash*`, `blocked`, `rotten`, `crowded`, `plan`) and type notes
  - `tv` / `movies` / `maybe_*` (superseded by records and `.base` views)
  - the 20 parentless files: a separate cleanup; the empty `Untitled*.md` and `.md`
    files are deletion candidates, pending Bryan's confirmation

### 6.5 Migration procedure (reliable, reversible)

1. Land the type note, `bob notebooks check`, and `sync` first, so migration output can
   be validated.
2. Generate a migration manifest (stem, new parent, summary, body edits). Run it through
   `bob notebooks check --dry-run`-style validation and show Bryan the diff before
   writing.
3. Apply it as one vault commit per root, so each is easy to revert, under the vault-sync
   lock (as `bob nightly` does).
4. Run `bob notebooks sync`, then re-run `check` with zero errors as the success
   criterion.

---

## 7. Alternatives considered

| Alternative | Why not (or not alone) |
| --- | --- |
| **Status quo: H2 sections in areas** | Does not scale (`dev.md` has 160 lines of tasks before any notes), nothing indexes it, and big sections bury task work. |
| **Small area notes instead of notebooks** | Areas drag in task machinery: Ready caps, `## Tasks` grouping, and a separate Stats root that fragments root-parent reporting. They also invite tasks. |
| **Folders** | Capture routes are root-only stems, and the vault is flat by convention (`parent` frontmatter). Folders would fork navigation. |
| **`@@nb…` as a separate sigil** (the original plan) | Collides with the draft-wide declaration (C1), leaves single-`@` behaviour undefined (C2), and needs new alias rules. The destination-decides rule gets the same expressiveness from forms that already exist. |
| **Pure live fence** (` ```bob-notebooks``` `) | Beautiful but invisible to graph view, backlinks, agents, and git. Obsidian mobile cannot spawn `bob`. Used here only as the *decoration* layer. |
| **Obsidian Bases embed per root** (`filter: parent == this`) | Native and zero-code, but direct children only: no rollup through sub-projects or nested notebooks, no real links, and a table look. Worth adding once, globally, on `notebook.md`. |
| **Record types** | Records are many schema'd one-item notes (restaurants, shows). A notebook is one free-form note of many bullets. These are different axes, and both have a place. |
| **Allow tasks in notebooks** | Breaks the "every task resides in exactly one area or project" invariant (glossary: Area Note) and recreates small areas. Use a later *promote note → task* gesture instead: it moves the bullet into the owner's `## Tasks` and leaves a link. |

---

## 8. Phasing, risks, and open questions

### 8.1 Phases

| Phase | Scope | Repo(s) | Size |
| --- | --- | --- | --- |
| 0 | Decision record and glossary term (via `/sase_memory_write`), `docs/notebooks.md`, `notebook.md` type note + `notebooks.base`, fix `capture.md:8327` | bob-cli, vault | S |
| 1 | Notebook recognition, `bob notebooks list/check/sync`, index writer, nightly step, `parent_candidates` and picker exclusions | bob-cli | M |
| 2 | Capture: destination-kind dispatch, sections (drawer rules), `+id` on notes, `^id`, `#sec^id`, refusals, `@@` inheritance, `%n` creation + in-batch index, parse modes, completion, ID default, `capture-rewrite` alias | bob-cli | L |
| 2m | Mac: icon, copy, modes, composer default pre-select | bob-mac-capture | S (macOS CI) |
| 2p | Plugins: callout CSS, live chips, Create notebook command, picker guards | bob-plugins | M |
| 3 | Extraction and moving with link repair: `bob notebooks extract`, Obsidian Extract and Move commands, capture move-in bullets | bob-cli, bob-plugins | M |
| M | Vault migration: Tier 1 with phase 1; Tier 2 after Q1/Q2; Tier 3 after phase 3 | vault | S–M |

### 8.2 Risks

- **Destination-dependent meaning.** Retyping a note flips what `@x` writes. Mitigations:
  the parse modes and live preview always show "📓 note → …", refusals teach the owner
  route, and notebooks never appear in task pickers.
- **Write amplification and sync conflicts.** Mitigations: stable-facts-only index text
  (A7), canonical rewrites only on structural change, the same all-or-nothing batch as
  capture, and vault-sync's same-point merge. The section is fully regenerable.
- **Link breakage on moves.** Extraction and moving must reuse the task-move link
  repair. Ship no move gesture without it.
- **Cross-repo contract.** Verified additive: Mac decodes `kind` and `mode` as strings
  with fallbacks. bob-cli ships first, per the thin-client decision.

### 8.3 Open questions for Bryan

- **Q1:** Homes for the `mind` and `own/home` strays. Should there be a `home` area
  (`grand_sanitation`, house notes)? Should `quote` go under `fun`, `love`, or a new
  `mind` area?
- **Q2:** Extracted legacy notebook names: keep your `legacy_<area>` pattern, or use
  capture's `<area>_legacy`?
- **Q3:** Default index placement: before `## Tasks` (recommended, visible on open) or at
  the end?
- **Q4:** Should leaf projects show their own Notebooks index (A6)?
- **Q5:** Should `_templates/new_note.md` start creating notebooks, given that
  `haircut`, `tv`, and `groceries` were all notebook-shaped?
- **Q6:** Should new notes append (chronological, recommended) or prepend (newest first)
  in idea notebooks?

---

## 9. Recommended solution

1. **Add `type: "[[notebook]]"`** as a third note kind with:
   - a required one-line `summary:`
   - a parent that is an area, project, or notebook
   - a hard **no-tasks** rule and soft bullet-and-H2 body rules
   - transparency to root walks
   - no Ready lanes, Stats roots, or review
2. **Let the destination decide in capture.** Do not add `@@` note forms. On a
   notebook:
   - `@nb` writes a top-level note.
   - `@nb#section` writes into a drawer-matched section, created on demand.
   - `@nb^id` and the new `@route#section^id` write a named note.
   - `@nb+id` writes under a note bullet.
   - `@@nb` declares notes draft-wide.

   All typing aliases work; the only new alias is `.`→`^` after `#section`. The block-ID
   composer pre-selects bob's suggestion. Task-only markers are refused with a rewrite to
   the owner route.
3. **Create notebooks with `@route^id@ %n <summary>`**, sharing project capture's seal,
   naming, and bullet-to-section mirroring. The `:` seal and `#pomodoro` are refused.
4. **Generate a `## Notebooks` index** in every area or project note, covering its
   subtree down to the next root parent (the requested root-parent rollup, plus leaf
   projects). bob writes a `[!notebooks]` callout of real wikilinks, titles, and
   summaries, with stable facts only. bob-ledger-tools makes it beautiful with CSS and
   live count and recency chips.
5. **Ship `bob notebooks list|check|sync|create|extract`**, with `sync` in `bob nightly`
   and in every creating batch. Extraction reuses task-move link repair.
6. **Migrate 18 Tier-1 notebooks across 8 roots in this change.** These include
   re-homing `sase_ideas` and `mac` out of the zorg tree and replacing `meet.md`'s
   hand-written index. Tier 2 follows Bryan's answers, and Tier 3 (the
   `## Legacy Notes` extractions) dogfoods `extract`. Never rename files; keep every
   `^z-…` ID.
7. **Record the rule** "Notebooks hold notes, never tasks; the destination decides what
   a route writes" as a decision. Add the **Notebook** glossary term from §5.
