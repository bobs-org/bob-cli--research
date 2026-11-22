# Drawers without ALL-CAPS: bold drawer headers, true-case titles, one place resolver

> **Research query:** Make task drawers stop requiring ALL-CAPS titles, without
> conflicting with the in-flight `bob-cli-on` (task requirements) epic. Find another way
> to mark drawer sub-bullets that does not mark the task the same way (does that rule out
> `#foo` tags?), render drawers in a distinct and easily recognizable way, and fix the
> capture syntax for drawers, reusing the notebook `##`-section targeting where that
> helps. The goals are true-case drawer titles and a step toward a lossless task ⇄
> project-note conversion. Critique the plan, call out any adjusted requirements, and end
> with a recommended solution.

Researcher: `cld` (one of five). Facts were verified on bob-cli `513ec478`,
bob-plugins `1e385218`, bob-mac-capture `bab5e5cc`, the live vault on 2026-11-22, and
the installed `bob 0.6.0`.

![Mock: the same task block stored with `**Future Work**`, rendered in Obsidian with a drawer-front glyph and a true-case semibold title, and typed in the Mac capture draft](drawers_without_all_caps__cld_assets/drawer_marker_mock.png)

_Figure 1: a design mock, not a screenshot. It shows the stored bytes, the proposed
Obsidian Live Preview, and the proposed Mac draft. Emoji on managed lines are omitted
because the mock renderer has no emoji font._

## Bottom line

**Yes, do it, and use Bryan's own instinct as the marker: a drawer is a bullet whose
entire text is one bold span (`- **Future Work**`), sitting directly under a task.** I
compared eight markers. Bold-only is the only one that keeps the title's real case and
punctuation, reads as a header with the plugins off, needs no new syntax, sits in the
same typographic family as Bob's managed lines (`🛠️ **WORK LOG**`), and maps one-to-one
onto a project note's `## Future Work`. The vault backs this up: only 3 task children
today are a bare bold span, and one of them, `**ROADMAP**`, is already a hand-made drawer.

Five refinements turn the idea into a reliable design. Each is argued below.

1. **One exact recognizer rule.** The bullet has no checkbox, and its trimmed body is
   `**` + title + `**`, where the title has no `*` and no inner leading or trailing
   space. Managed lines and reserved names are matched first. **Children are not
   required.** 53 of the vault's 109 eligible project `##` sections are empty, and a
   lossless round trip needs an empty `## Notes` to map to an empty `- **Notes**`.
   Capture still never *creates* an empty drawer.
2. **Drawers keep their real name everywhere, with no re-casing.** Promotion becomes
   `- **API Design**` → `## API Design`, and demotion is its exact inverse. Today
   promotion turns `API DESIGN` into "Api Design", and demotion refuses `## C++ Notes` or
   `## Q1: Goals` outright.
3. **One "place" resolver for capture.** Task drawers, `^prj` sections, and notebook
   sections share one selector lexer, one matching ladder, and one create-title rule.
   The create-title rule is the notebook's: keep typed capitals, title-case the rest,
   and keep quoted titles verbatim. Task drawers additionally prefer the drawer
   catalog's spelling. `- #api-design` stays the typing shortcut, and the menu writes
   `- **API Design**` so the draft still mirrors the block.
4. **Render through the shape grammar Bob already uses.** Today it is square = task,
   ring = Task Link, and diamond = requirement (as the req display redesign proposes).
   A drawer gets a small **drawer-front** glyph in the owner's ink, with the title in
   semibold and its true case. A folded drawer shows a count, and an empty one is
   dashed. The plugins add a glyph and never change the words.
5. **Decide now, but ship after the epic's in-flight phases.** `bob-cli-on.11`, `.12`,
   and `.17` are editing the same promotion code, task-split predicate, vectors, and
   glossary strand. A short dual-read window, followed by a gated seven-line vault
   migration, makes the cutover safe across hosts.

Adjusted requirements are called out in [Adjustments](#adjustments-to-the-requirements).
The full recommendation is in [Recommended solution](#recommended-solution).

## What ships today

### The recognizer, and where ALL-CAPS is hard-coded

bob-cli has one predicate, `capture_drawers::is_drawer_title`
(`src/native/capture_drawers.rs:1596`). It requires a leading `A-Z` or `0-9`, then
`A-Z 0-9`, space, `& ' ( ) , . / - ? ! ;`, an optional trailing `:`, and at least one
`A-Z`. Keys are uppercased (`drawer_key`, `:76`), so **matching is already
case-insensitive**. Only *recognition* and *creation* depend on caps. Every write path
uppercases:

- `normalize_drawer_literal` uppercases quoted literals (`:69`);
- `drawer_spelling_for_slug` falls back to uppercase (`:1279`);
- `lexical_title_for_slug` uppercases (`drawer_bullet.rs`);
- the bullet menu row inserts `drawer_key(title)`, the bare uppercase key
  (`capture_complete/drawers.rs:412-425`).

Callers that inherit the rule:

| Surface | Site | What depends on ALL-CAPS |
| --- | --- | --- |
| Task child classification | `task_children.rs:131` | `TaskChildKind::Drawer` |
| Requirement structure | `task_reqs.rs:283` | drawer = structural container |
| Block layout and writers | `task_block_layout.rs:64` (`NOTES_TITLE = "NOTES"`), `writers.rs:518` | NOTES drawer, `req_in_drawer` |
| Drawer rename | `task_drawer_rename/mod.rs:328,770,939` | OLD matching, NEW "in catalog casing" |
| Capture draft drawer literal | `drawer_bullet.rs:451` `is_all_caps_drawer_title` | ALL-CAPS + nested = drawer |
| Project-note capture | `capture_project_note.rs:236-263,464` | ALL-CAPS bullet → `## Title Case` ("acronyms are not preserved") |
| Notebook `%n` seeds | `section_bullet.rs:440,626` | ALL-CAPS bullet → `##` seed |
| Record capture | `capture_language/record.rs:851` | ALL-CAPS bullet → section group |
| gcal descriptions | `gcal/description/bullets.rs:140-141` | **wraps an ALL-CAPS line in `**…**` to defuse it** |

Outside bob-cli, a subagent inventory that I spot-checked found **four hand-written
copies** of the predicate in bob-plugins:

- `taskReqIsDrawerTitle` in nav-hotkeys `694-task-reqs-lines-twin.js:365`, plus two
  byte-identical twins;
- `isTaskSplitDrawerTitle` in `256-task-split-plan.js:23-80`, which also gates promotion
  and demotion;
- a separate regex in bob-ledger-tools `139-task-reqs.js:128`. I verified it with `node`:
  `\/-?` is a character range, so it also accepts `NOTE: X`, `A<B`, and `KEY:: VALUE`,
  which Rust rejects.

Promotion title-cases (`100-yank-and-paths.js:851-870`). Demotion uppercases the `##`
title and refuses the whole reversal when the result is not a valid ALL-CAPS title
(`:689-698`, `210-rename-and-line-context.js:718`). On the Mac, transfer and merge
previews call `.uppercased()` (`CaptureTransferPresentation.swift:647`,
`CaptureMergeInPresentation.swift:268`). **No plugin CSS styles drawers at all**: today
a drawer looks like any other bullet whose text happens to be shouted.

The epic plan's §10 says `^no-all-caps-for-drawers` is "one change in one place". That
is true only for Rust recognition. The real surface is one Rust predicate with about 12
callers, four JS copies, the gcal defuser, the casing functions on both sides of
promotion, two Mac call sites, fixtures, and docs.

### Verified behavior in a scratch vault (`bob 0.6.0`)

```text
foo.md:  - [ ] #task Upgrade Postgres ^bar
         	- **Future Work**
         		- try replication

$ bob capture --dry-run '@foo+bar#"Future Work" Try logical decoding'
  under [ ] Upgrade Postgres ^bar · FUTURE WORK   new drawer    ← duplicate by intent

$ bob capture --dry-run $'@foo+bar\n- AWS\n  - us-east-1 only\n- #api-design\n  - REST first'
  AWS          new drawer      ← an acronym note silently became a drawer
  API DESIGN   new drawer      ← typed "api-design", got shouting
```

All three failure modes Bryan is reacting to are real. True case cannot be stored, an
ALL-CAPS note with detail becomes a drawer, and a hand-written bold header is invisible
to Bob.

### Vault inventory (scan of `~/bob`, 2026-11-22)

- **ALL-CAPS task drawers:** 7 (5 in live notes, 2 in `done/`). They are `NOTES` ×3 and
  one each of `NOTES:`, `OPTIONS:`, `MOTIVATION`, and `DONE`. None is childless.
- **Task children whose whole body is bold:** 3.
  - `**ROADMAP**` with children (`done/sase_done.md:393`), already used as a drawer;
  - `**Or just use task dependencies for this?!**`, childless emphasis (`done/`);
  - `**Note:**`, childless, imported by gcal (`2026/20261113.md:31`).
- **Other bold-led children:** 7 (`**RELATED:** …`, `**SOLUTION**: …`). None is
  whole-bold, so none is affected.
- **Project notes:** 103 notes with 109 eligible `##` sections. There are 0 ALL-CAPS
  `##` headings, **53 empty sections** (30 `## Notes`, 23 `## Future Work`), 2 sections
  with non-bullet prose, and 2 with `###` subsections.

## Is this a good idea?

**Yes. ALL-CAPS overloads one property, letter case, with two jobs: content and
structure.** Every bug above comes from that overload.

- True case is unrepresentable. "API Design", "iOS", "C++ Notes", and "Café" cannot
  exist as drawers.
- Any shouted note with detail, such as `- AWS`, `- TODO`, `- LGTM!`, or `- DONE`,
  silently becomes a drawer. Under requirements, that changes block layout and the
  `req_in_drawer` refusals.
- Promotion and demotion must re-case, so they are lossy in both directions. Today
  `## API Design` → `- API DESIGN` → `## Api Design`. That blocks the stated larger goal,
  `^task-to-project`, which needs every project note to have a lossless task form.
- ALL-CAPS reads as shouting next to quiet notes, and the redesigns of requirements and
  link marks are moving Bob toward quieter shapes.

**Would I take a different approach?** I would keep Bryan's marker, `**Title**`, but
change four things about how the request is framed:

1. **Specify the marker as a precise structural rule.** "Use bold" is not enough: it
   needs an exact recognizer, a defined precedence against managed lines, and an
   escape. Bold is common emphasis, and Bob's own gcal writer emits bold today.
2. **Treat it as a container-marker swap across capture, not only a drawer change.**
   ALL-CAPS-with-children means "named container" in four capture contexts: task
   drawers, project-note capture, notebook `%n` seeds, and record groups. Swap all four,
   or ALL-CAPS stays magic in some drafts and not others.
3. **Make "reuse the notebook logic" mean one resolver, not copied rules.** The two
   bullet lexers (`drawer_bullet::scan_leading` and `section_bullet::scan_leading`) are
   already near-verbatim duplicates. The two resolvers differ mainly in casing.
4. **Sequence the work after the epic phases that touch the same files.** Do not
   interleave it with them.

## Does this rule out `#foo` tags?

**Yes, and for stronger reasons than "it would mark the task too".**

- **Tags cannot hold the title.** Obsidian tags cannot contain spaces and most
  punctuation, so `#Future_Work` is not "Future Work". That defeats the change's first
  goal outright.
- **Tags are global.** Obsidian indexes every tag vault-wide. Each drawer name would
  join the tag pane and tag search beside `#task`, `#prj`, `#hide`, and type tags, which
  is noise at best.
- **`#` is already overloaded in Bob.** A glued `#` names a place, and a free `#` names
  a type ([[decisions:capture-sigils-say-where-what-how]]). A third, on-disk meaning
  would make `- #fix` ambiguous in both the vault and the draft.
- **It would mark the task.** Bryan's instinct is right: readers that collect tags from
  a block, as well as Obsidian's tag search, would associate the tag with the task
  rather than with a labeled container.

## Choosing the on-disk marker

Criteria, in priority order:

1. keeps true case and punctuation;
2. unambiguous: low false positives, and no collision with Bob's grammar, managed lines,
   Dataview, or Tasks;
3. reads as a header with the plugins off (raw, GitHub, mobile);
4. maps losslessly to `## Title`;
5. easy to type;
6. beautiful.

| Marker | True case | Unambiguous | Plugins-off | `##` mapping | Typing | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| ALL-CAPS (today) | ✗ | ✗ (`- AWS` + child) | ✓ shouts | lossy | Ctrl-G U | retire |
| `#tag` | ✗ (no spaces) | ✗ (type/place `#`, global index) | ~ | lossy | easy | reject |
| **`**Title**` (bold-only)** | ✓ | ✓ with the exact rule; 3 hits in the vault | ✓ bold header | **identity** | `*` assist | **choose** |
| `- ## Title` (heading in a list item) | ✓ | ~ | ✓ but loud | identity | easy | reject: revives the `##` look the req redesign is removing; heading chrome in task lists; risk of polluting outline and `[[note#Heading]]` resolution (unverified) |
| `Title:` (colon suffix) | ✓ | ✗ (13 short colon-ended notes under tasks today) | ✗ | ~ | easy | reject |
| `🗂️ **Title**` (emoji + bold) | ✓ | ✓✓ | ✓ | identity | needs assist | runner-up: emoji means "Bob-managed" today, and it adds noise the plugin glyph already provides |
| `[drawer:: Title]` | ✓ | ✓ | ✗ ugly | ~ | heavy | reject (Dataview field) |
| Fixed vocabulary (no marker; config lists `Notes`, `Future Work`) | ✓ | ✗ (`- Done` note) | ✗ | identity | none | reject: ad-hoc drawers need config edits |
| A different list marker (`+ Title`) | ✓ | ✗ | ✗ invisible | ~ | ~ | reject: CommonMark starts a new list |

`**Title**` also completes a clean "one shape per child kind" table on disk:

| Task child | On-disk shape |
| --- | --- |
| Subtask | `- [ ] #task …` |
| Requirement | `- [ ] …` (checkbox, no `#task`) |
| Managed link or log | `- ⛓️ **DEPENDS ON:** …`, `- 🛠️ **WORK LOG**` (emoji + bold label) |
| **Drawer** | **`- **Future Work**` (bold label, no emoji)** |
| Note | anything else |

Bold means "this line is a label". An emoji in front means "Bob owns this label". That
rule is easy to teach.

## The recognizer, precisely

A **drawer** is a list item that meets all of these:

1. It is a direct child of a `#task` line, outside fences and quotes. On a project
   note's own `^prj` task, the drawers remain the note's eligible `##` sections, as
   today.
2. It has no checkbox. A `- [ ] **X**` line is a requirement, as today.
3. Its trimmed body is exactly `**` + *title* + `**`, where the title:
   - is nonempty;
   - has no leading or trailing whitespace inside the delimiters (CommonMark would not
     render `** X**` as bold anyway);
   - contains no `*`;
   - has nothing outside the delimiters: no trailing `^id`, tag, or field.
4. It is not a managed line (those matchers run first). Its key is not reserved (`TASKS`,
   `WORK LOG`, `LINKS`, …), as `reserved_drawer_keys` derives today. So a hand-typed
   `- **Work log:**` stays a legacy managed log, exactly as now.
5. **It needs no children.** Empty drawers are valid. Capture still never creates one,
   so "nonempty by construction" survives.

**Title** is the inner text, verbatim; that is what gets stored and rendered. **Key** is
the whitespace-collapsed title, uppercased, the same function as today, so `NOTES`
keeps working as the NOTES-drawer key, catalogs carry over, and `**Notes**` with
`**NOTES**` under one task is `ambiguous_drawer`, as now. One optional nicety: drop a
single trailing `:` from the key, so `**Notes:**` and `**Notes**` never split.

| Line under a task | Today | Proposed |
| --- | --- | --- |
| `- **Future Work**` + notes | note | **drawer "Future Work"** |
| `- **API Design**` (no children) | note | **empty drawer** (capture fills it instead of duplicating) |
| `- FUTURE WORK` + notes | drawer | note (after the cutover) |
| `- AWS` + notes | drawer (false positive) | note |
| `- **Note:** call back` | note | note (trailing text) |
| `- __Note:__` | note | note (the documented escape: renders identically bold) |
| `- **Work log:**` / `- **LINKS**` | managed / reserved | managed / reserved |
| `- [ ] **Ship it**` | requirement | requirement |
| `- ***Wow***` | note | note (`*` inside) |

**Why children are not required.** Requiring a child would look attractive because it
removes the two childless bold notes in the vault. But it breaks the lossless goal: 53
of 109 project sections are empty, so demoting `## Future Work` (empty) would give a
childless `- **Future Work**`, which would then promote as a *note*. It would also make
"type a header, then capture into it" create a duplicate. Today's vault recognizer
already accepts childless drawers (`parse_drawer_title`'s comment explains why). Only
two places require children today: the capture draft's ALL-CAPS literal, which stays
that way as "capture never creates an empty drawer", and the plugin promotion, whose
requirement goes away.

**Requirements are unaffected by construction.** A checkbox under a note *or* under a
drawer is never a req (both break the owner chain), so reclassifying a line between note
and drawer never changes req identity. This confirms the epic's own claim that "req
identity never depends on title casing". What does change is block zone placement and
which refusal copy fires (`req_in_drawer` versus `req_parent`).

## Rendering

**Principle: the plugin adds a glyph and never changes the words.** With the plugins on
or off, the title reads in its true case, in bold.

**Obsidian** (bob-ledger-tools, beside the requirement marks):

- **Attributes.** A Live Preview `Decoration.line` (at `Prec.highest`, using the
  Blocked-Marks and requirement pattern) and a reading-view attribute post-processor add
  `data-bob-drawer`, `data-bob-drawer-key`, `data-bob-drawer-count`,
  `data-bob-drawer-empty`, and the owner's type attributes. Neither creates DOM nodes.
- **Glyph.** The bullet dot becomes a **drawer front**: a small wide rounded rectangle
  with a centered handle, drawn as a CSS mask in the owner's type ink (teal by default).
  Bob's shapes then read: square = task, ring = Task Link, diamond = requirement (as
  proposed in `research:202611/task_reqs_display_redesign/…`), dot = note, drawer front
  = drawer. Every glyph is distinct in silhouette and in grayscale.
- **Title.** Semibold, normal text colour, true case. I considered `small-caps`: it
  echoes the old look while keeping the case distinction, but it hides the very
  capitalization this change exists to show. I recommend against it.
- **Folded.** Obsidian's fold works unchanged. A folded drawer shows a muted
  `· {n} notes` after the title, from `data-bob-drawer-count`.
- **Empty.** The glyph is dashed, the title muted, and a hint reads `· empty`.
- **Raw bytes.** With the cursor on the line, Obsidian already reveals the raw `**`.
  The tag-marks session toggle restores plain bold.
- **Tooltip and accessible label.** `Drawer “Future Work” · 2 notes · in “Upgrade
  Postgres”`.

**Plugins off, GitHub, and mobile:** a bold header line with notes beneath it. That is
the right fallback, and better than ALL-CAPS.

**Mac capture draft:**

- `capture-parse` adds a `drawer_marker` span over each `**` delimiter, next to the
  existing `drawer_bullet` span. The Mac paints the title in its section colour,
  semibold.
- I recommend **dimming the `**` rather than hiding them**, with a caret-adjacent
  reveal. Epic note #6 found that the Mac's `req_marker` concealment has no caret
  reveal, so the caret walks invisibly across hidden cells. Do not copy that defect.
- Drop `.uppercased()` in the transfer and merge presentations.
- The Ctrl-G U case toggle stops being the way to type drawers.

**CLI and cards:** human output prints `· Future Work` and `new drawer Future Work`, never
an uppercased title. Requirement and successor cards carry the title through as-is.

## Capture syntax: reuse the notebook section logic

### What to reuse, and what not to

The notebook resolver (`resolve_notebook_section`, `notebook.rs:246`) and the drawer
resolver (`resolve_drawer_for_write`, `capture_drawers.rs:1017`) already solve the same
problem: find or create a named container of notes. They differ in four places:

| Concern | Notebook `##` section | Task drawer / `^prj` section |
| --- | --- | --- |
| Create from a slug | typed capitals kept, other words Title Case (`format_notebook_section_create_title`, `:399`: `#API-keys` → `API Keys`) | catalog spelling, else **UPPERCASE** |
| Quoted literal | verbatim | **uppercased** |
| Near-miss | prefix or edit distance ≤ 2, refuse and suggest | prefix or edit distance 1 refuses; distance 2 against the catalog warns |
| Extras | — | vault-wide catalog (spellings, recents), reserved and structural keys |

**Recommendation: one `place` resolver with a `scope` parameter** (`TaskDrawer`,
`ProjectSection`, `NotebookSection`; record sections can join later). It has:

- **One lexer** for the bullet-start `#` and the glued `#`, merging
  `drawer_bullet::scan_leading` and `section_bullet::scan_leading`. Context decides the
  meaning, as it does today.
- **One ladder.** Match an exact key, else match the whole slug. Then check ambiguity
  (naming every line), then reserved or structural keys for the scope, then the
  near-miss refusal, which suggests the existing title and offers the quoted override.
  Otherwise create.
- **One create-title rule.** A quoted title is kept verbatim (whitespace collapsed). A
  slug takes the **catalog's most-used spelling** when the scope has a catalog (task
  drawers and `^prj` sections); otherwise it takes the notebook rule: keep typed
  capitals and title-case the rest.
- **Scope parameters** carry today's near-miss thresholds and nouns, so the merge
  changes nothing but casing. A later vector pass can converge the thresholds.

This also deletes code. `DrawerScope::ProjectSection`'s "promotion Title Case on
creation" (`cased_creation_title`) disappears: a drawer and its `##` section now have
the same title.

### The draft forms

The principle ([[decisions:capture-bullets-mirror-the-task-block]]) is that the draft
reads like the block it writes.

| Draft | Writes |
| --- | --- |
| `- **Future Work**` + nested notes (first level, in a drawer position) | the drawer, title verbatim; merges by key into an existing drawer and keeps its spelling, with the preview showing which |
| `- #future-work` / `- #API-design` / `- #"Q1: Goals"` + nested notes | the shortcut: resolves through the place ladder. **Menu acceptance rewrites the bullet to `- **Title**`** (plus `  - ` when no nested bullet follows), exactly as it writes the bare ALL-CAPS title today |
| `@foo+bar#future-work note`, `@foo+bar#"Future Work" note` | glued selector, same ladder; creates `**Future Work**` |
| `--drawer "Future Work"` | exact, verbatim |
| Project-note capture `@x^id@` with `- **Design**` + nested | `## Design` verbatim (was ALL-CAPS → Title Case) |
| Notebook `%n` with `- **Git**` + nested | `## Git` seed (was ALL-CAPS seed → Title Case) |
| Record capture with `- **Notes**` + nested | that section group (was ALL-CAPS) |
| Route-only `@nb` list with `- **Git**` + nested | **unchanged: a note with detail.** Use `- #Git` for sections. This keeps the notebook decision's deliberate `@nb`/`%n` split |
| `- FUTURE WORK` + nested | a note with detail, plus a one-release `caps_drawer_retired` warning: ``ALL-CAPS no longer makes a drawer — write `- **Future Work**` or `- #future-work` `` |

`*` sigil safety: the blocking-sigil grammar already treats `**bold**` as literal (rule
2 in `docs/capture.md`, "the byte after `*` is neither whitespace nor `*`"). The
drawer form collides with nothing.

### Typing assists (Bryan's `*` → `**|**`)

- **Expansion.** `capture-rewrite` gets a new rule, `expand_drawer_marker`, and Obsidian
  gets a twin. Typing `*` into an **empty** bullet body *in a drawer position* produces
  `**|**`. In Obsidian a drawer position is a direct child of a task. In capture it is
  a first-level bullet under a new task, a new project note, or a note-less
  `@route+id`.
- **Overtype absorption.** Typing `*` immediately before the closing `**` steps over
  both stars, using the same provenance absorption the req `]` uses.
- **Enter completes.** Enter with the caret at the end of the title moves past `**` and
  opens the first nested note (`\n\t\t- ` in Obsidian, `\n  - ` in capture), so
  `* Future Work ⏎` lands you inside the drawer.
- **Atomic Backspace.** Backspace inside an empty `**|**` removes both pairs and leaves
  `- `.
- **Undo** restores `- *`.
- **What never rewrites.** Paste, templates, and `bob capture` itself never rewrite, as
  with every other alias.
- **Obsidian's auto-pair.** Obsidian's "Auto-pair Markdown syntax" setting already pairs
  `*`, so the assist must compose with it, as the req assist does with
  `autoPairBrackets`.

### Grammar and wire

- Bump `GRAMMAR_REVISION` (29 → 30, or whatever is next) with a `!` commit. Two breaks:
  an ALL-CAPS bullet with nested notes is no longer a drawer, and quoted literals keep
  their case.
- Wire additions are all additive:
  - the `drawer_marker` span kind;
  - menu `replacement` values that now carry `**Title**`;
  - drawer objects that report `title` verbatim plus `key`.
- Bump the drawer catalog to `DRAWER_CATALOG_VERSION = 3`, so spellings are rescanned
  under the new recognizer.

## Promotion and demotion: the lossless step

| Direction | Today | Proposed |
| --- | --- | --- |
| Promote `- **API Design**` (or legacy `- API DESIGN`) | needs children; `API DESIGN` → `## Api Design` | `## API Design` verbatim; an empty drawer becomes an empty section; merges into an existing `##` by key, keeping that heading's spelling (today's rule) |
| Demote `## API Design` | uppercases to `- API DESIGN`; **refuses the whole reversal** for `## C++ Notes`, `## Q1: Goals`, `## Café` | `- **API Design**` verbatim; refuses only a title containing `*`, or a reserved or structural key |
| `NOTES` / `**Notes**` ⇄ `## Notes` | `## Notes` (re-cased) | identity |

The epic's `.12` phase writes "Other drawers → `## Title Case` sections (unchanged)".
This change replaces "Title Case" with "verbatim". `formatProjectSectionTitle` and
`format_project_section_title` survive only to read legacy ALL-CAPS drawers during the
dual-read window.

**What stays lossy for `^task-to-project`** (out of scope here, but worth seeing): prose
paragraphs inside sections (2 sections in the vault), `###` subsections (2), the H1 and
preamble, and frontmatter keys (`offclock`, `task_type`, `summary`, …).

A natural next stone is `###` ⇄ a bold header nested *inside* a drawer. Keep that shape
free now: a whole-bold bullet inside a drawer stays an ordinary note and gets no other
meaning in the meantime.

## Outside text never becomes a drawer

Today gcal *defuses* an ALL-CAPS description line by wrapping it in bold
(`bullets.rs:140-141`). After this change, **that defuse would create a drawer.** Flip it:

- ALL-CAPS lines pass through untouched, because they are just text now.
- A whole-bold description line is written as `__…__`. Obsidian and GitHub render it as
  the same bold, and it is never a drawer.
- Apply the same rule in `task_text_escape::escape_child_text` (gkeep, gmail,
  highlights) and to `%c` clipboard notes. Record it in the contract next to the req
  epic's rule: "Pasted text never becomes a requirement **or a drawer**."
- Vault exposure is one gcal `**Note:**` child plus one childless emphasis note in
  `done/`. The migration report lists both and proposes `__…__`.

Note that gcal's span hash covers the *rendered* bodies, so changing the renderer
rewrites untouched Google spans on their next sync. That behavior is intended and is
covered by "updates only untouched Google spans".

## Conflicts with the `bob-cli-on` epic

The epic is 13 of 17 phases closed. Four are in progress: `.11` Obsidian successor card
and carry-now, `.12` promotion, `.15` Mac Pull-In card, and `.17` memory.

| Epic item | Status | Overlap with this change | Action |
| --- | --- | --- | --- |
| `.11` obsidian-close-card | in progress | edits `256/257/259` task-split, which hosts `isTaskSplitDrawerTitle`; re-copies `task_split/vectors.json` | start after it lands |
| `.12` promotion | in progress | **the same promotion code** (`110`, `100`, `667`), and it pins Title Case | send one instruction now: keep the drawer test and section casing behind `parseProjectSectionBulletTitle` and `formatProjectSectionTitle` only, so this change becomes a two-function swap; start after it lands |
| `.15` mac-close-card | in progress | Mac fixtures only | start after it lands, to avoid fixture churn |
| `.17` memory | in progress | rewrites `glossary:task-drawer` in ALL-CAPS-era wording | this change's memory decisions come after it and correct it |
| Epic notes #2 and #4: the `^prj` NOTES home | open finding | `ensure_drawer`'s `is_prj_parent` path appends `## NOTES` at EOF with tab-indented children and duplicates the heading on every write | same code. Fix it **once**, before or inside phase 1 here; the created heading becomes `## Notes` |
| RQ/RL/RW/SP vectors | shipped | contain ALL-CAPS drawers | update in bob-cli first, then re-copy into every twin |
| `NOTES` key, zones, `req_in_drawer` | shipped | unchanged; the key stays `NOTES`, and the writer spells it `**Notes**` | none |
| Grammar 29 | shipped | this change bumps the grammar again | none |

Nothing in the epic's *behavior* conflicts with this change. The conflicts are file and
vector contention, plus one shared bug.

## Migration and rollout

1. **Dual-read release** (bob-cli, plugins, Mac). Readers accept both the bold and the
   legacy ALL-CAPS drawer forms; every writer writes bold. Capture's grammar flips with
   the `caps_drawer_retired` warning. Any host order is then safe: the notebooks
   precedent says "every host must run [the new] bob before any vault retype".
2. **Gated vault migration.** Reuse the epic's design call 7: the migration is approved
   runs of the general command, not a script.
   - Extend `bob task rename-drawer OLD NEW` so it:
     - writes NEW verbatim in the bold form;
     - allows a case-only respelling (equal keys, different spelling);
     - has an inventory mode listing every legacy ALL-CAPS drawer.
   - Five runs cover the vault: `NOTES→Notes`, `NOTES:→Notes:` (or merge into `Notes`;
     Bryan's call), `OPTIONS:→Options:`, `MOTIVATION→Motivation`, `DONE→Done`.
   - The report also lists the two childless whole-bold notes.
   - Everything runs as a dry run first, then goes to Bryan through `/sase_gate`.
3. **Cutover release.** Once the inventory reports zero, remove ALL-CAPS recognition,
   the gcal ALL-CAPS defuse, the legacy casing helpers, and the legacy vectors.

## Adjustments to the requirements

- **ADJ-1: Decide now, ship after `.11`, `.12`, `.17` (and `.15`).** One instruction goes
  to `.12` now (see the conflict table). This mirrors the req display redesign's
  "decide now; ship after the epic".
- **ADJ-2: No re-casing anywhere.** The request says "represent the true capitalization
  in drawers". The lossless goal needs more: promotion and demotion must stop
  re-casing, and demotion must stop refusing mixed-case and punctuated sections. This
  changes `.12`'s pinned "`## Title Case`".
- **ADJ-3: Empty drawers are valid drawers.** Recognition does not require children
  (53 empty project sections), while capture still never creates an empty drawer. A
  stricter "bold + children" rule would quietly break round trips.
- **ADJ-4: Scope the `*` assist to drawer positions.** Bryan said "at the start of a
  sub-bullet". Firing it under notes and reqs too would ambush italics for no benefit.
  Add the Enter-completes and atomic-Backspace behaviors so typing a drawer is one
  motion.
- **ADJ-5: Swap the marker in all four ALL-CAPS container contexts** (task drawers,
  project-note capture, `%n` seeds, record groups). Leave the `@nb` route-only list
  semantics alone. "Reuse the notebook logic" means the shared resolver and
  create-title rule, not making bold bullets into sections everywhere.
- **ADJ-6: Extend the outside-text rule to drawers.** Flip the gcal defuse and add the
  `__…__` escape. Without this, the change creates drawers out of imported text.
- **ADJ-7: Cut over in three steps.** "No longer need to be capitalized" happens as dual
  read, then a gated migration, then removal; it is not an instant switch.

## Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Emphasis bullets under tasks become drawers | Exact whole-span rule, so any trailing text keeps a note; the `__…__` escape; 3 cases in the vault, listed in the migration report |
| Managed-label collisions (`**Links**`, `**Work log:**`) | managed matchers run first; reserved keys refuse in capture (existing machinery) |
| Five JS copies drift again (one already has a regex bug) | One bob-cli-owned `tests/fixtures/drawers/vectors.json` (DV1…). Collapse to **one** JS predicate twin, copied byte for byte and enforced by the existing twin-copy check. Task-split and ledger-tools import or copy it |
| Version skew across athena, apollo, and the Mac | dual-read release before the migration |
| `*` assist versus Obsidian auto-pair, Vim, or the `*T` blocking sigil | compose with auto-pair; fire only in drawer positions on an empty body; Undo restores `- *`; `- *T` on its own bullet line is the one edge, and it is rare |
| Case-only duplicates (`**Notes**` + `**NOTES**`) | `ambiguous_drawer` (existing); `bob task tidy` can report them |
| Old bob reading the migrated vault | gated on every host running the dual-read release |
| Hidden delimiters on the Mac | dim them and reveal at the caret; do not copy the req conceal defect |

## Side findings

1. **ledger-tools drawer regex bug** (`139-task-reqs.js:128`). `\/-?` is a range from
   `/` to `?`, so the regex accepts `NOTE: X`, `A<B`, and `KEY:: VALUE` as drawer
   titles, unlike Rust. I verified it with `node`. It is benign for requirements today
   (a checkbox under a note or a drawer is never a req), but it is the drift this change
   should end.
2. **The epic plan's §10 "one change in one place"** understates the surface. See the
   inventory above.
3. **Hand-written bold headers are ignored, and capture duplicates them.** `@foo+bar#"Future
   Work"` next to an existing `**Future Work**` creates `FUTURE WORK` (verified). This is
   the most user-visible bug the change fixes.
4. **Name clash.** The `bob-cli-pf` epic's card "Properties drawer" (`=-`) and the Task
   Drawer share a word. The glossary should keep them apart ("task drawer" versus
   "card drawer").

## Recommended solution

**Store a drawer as a bullet that is exactly one bold span, `- **Title**`, directly
under a task. Keep the title verbatim, key it case-insensitively as today, allow empty
drawers, never let capture create one, and match managed lines first.** Render it in
Obsidian as a drawer-front glyph in the owner's ink with a semibold, true-case title,
with a folded count and a dashed empty state. Dim the delimiters in the Mac draft. With
the plugins off it is a bold header. Promote and demote verbatim
(`- **API Design**` ⇄ `## API Design`). Capture reuses the notebook section logic
through one place resolver: typed capitals kept, quoted titles verbatim, and the catalog
spelling preferred for task drawers. `- #slug` stays the shortcut that writes
`- **Title**`, and `*` expands to `**|**` in drawer positions.

Phases, all after `bob-cli-on.11`, `.12`, and `.17` land:

1. **drawer-contract** (bob-cli).
   - `drawer_header(body) -> Option<&str>`, with dual-read of legacy ALL-CAPS.
   - DV vectors and a contract section in `docs/capture.md` and
     `docs/task-requirements.md` (NOTES spelled `**Notes**`).
   - Retarget all ~12 Rust callers and drop every uppercasing creator.
   - Writers emit bold.
   - Fix the `^prj` NOTES home if it is still open.
   - Flip the gcal defuse and add the `__…__` escape.
   - Catalog version 3.
2. **place-resolver** (bob-cli, plans first).
   - Merge the lexers and resolvers.
   - Bold literals in all four container contexts.
   - Menu rows write `**Title**`.
   - The `expand_drawer_marker` rewrite and the `drawer_marker` span.
   - The `caps_drawer_retired` warning and the grammar bump (`!`).
3. **rename-drawer respell** (bob-cli). Verbatim NEW, case-only respelling, and the
   legacy inventory.
4. **plugins** (nav, cycler, block-id-prompt, ledger-tools).
   - One predicate twin.
   - Verbatim promotion and demotion.
   - Drawer marks (attributes, CSS, glyph, count, empty).
   - The `*` assist with Enter and Backspace.
   - NOTES writers emit `**Notes**`.
5. **mac** (bob-mac-capture).
   - Decode the `drawer_marker` span; dim and reveal.
   - Drop `.uppercased()`.
   - Wire the assist into `capture-rewrite`.
   - Regenerate fixtures.
   - Watch the macOS run on the exact SHA.
6. **vault-migration** (gated). Five `rename-drawer` runs plus the bold-note report.
7. **cutover** (bob-cli and plugins). Remove legacy recognition and casing once the
   inventory reads zero.
8. **memory** (decisions for the future plan, per `/sase_memory_write`). I edited no
   memory; these are the decisions the plan should carry.
   - `glossary:task-drawer`: default **yes**, because the work makes this claim false:
     `corrects:` "A direct non-checkbox ALL-CAPS child bullet of a `#task` line".
     Re-copy the quote at plan time, since `.17` may reword the strand first.
   - Mark [[decisions:capture-bullets-mirror-the-task-block]] superseded in part:
     default **yes**, because the work makes this claim false: `corrects:` "There an
     ALL-CAPS title with nested notes is a [[glossary:task-drawer]]".
   - A new decisions record, "Drawers Are Bold Headers With Their Real Names", which the
     mark above would point to: default **no**, because it is an addition rather than a
     correction. Bryan decides; if he declines, the mark's back-link points at the
     glossary strand instead.
   - Marking [[decisions:capture-sigils-say-where-what-how]] (quoted-literal casing):
     default no unless Bryan asks.

The live test: write five real tasks with drawers like "API Design", "Q1: Goals", and
"Notes". Promote one and demote it back, then capture into each drawer from the Mac.
Success means every title survives byte-for-byte, nothing shouts, and Bryan can tell a
drawer from a note at a glance without reading the docs.

## Evidence

- Code: bob-cli `src/native/capture_drawers.rs`, `task_children.rs`, `task_reqs.rs`,
  `task_block_layout.rs`, `capture_language/{drawer_bullet,section_bullet,notebook,record}.rs`,
  `capture_project_note.rs`, `capture_complete/drawers.rs`, and
  `gcal/description/bullets.rs`. bob-plugins nav `100`, `110`, `210`, `256`, `694–698`,
  and ledger-tools `139`. bob-mac-capture `CaptureTransferPresentation.swift`,
  `CaptureMergeInPresentation.swift`, and `CompletionRowContent.swift`.
- Docs: `docs/capture.md` (Authored sub-bullets, Notebook notes, Sub-bullets under
  existing tasks, Blocking with `*`), `docs/projects.md` (promotion and reversal), and
  `docs/task-link-marks.md` ("Identity by shape, state by fill").
- Plans and research: `plan:202611/task_requirements.md` (§§3, 8, 10, and phases),
  bead `bob-cli-on` (notes #2, #4, #6), and
  `research:202611/task_reqs_display_redesign/task_reqs_display_redesign.md`.
- Memory: [[glossary:task-drawer]], [[glossary:notebook]],
  [[decisions:capture-bullets-mirror-the-task-block]],
  [[decisions:notebook-routes-write-notes]], and
  [[decisions:capture-sigils-say-where-what-how]].
- Vault: `~/bob/bob.md` `^no-all-caps-for-drawers` ("Use `**Title Text**` for this! The
  `*` character should expand to `**<cursor>**`…"), plus the scans described above.
- Runtime: `bob 0.6.0` dry runs in a scratch vault, and a `node` check of the
  ledger-tools regex.
