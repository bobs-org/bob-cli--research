# An `## Areas` catalog for area notes and `area.md` — design research (cld)

> **Research query:** We already render an H2 "Projects" section in area/project notes
> that are parents of one or more project notes. Start rendering a new "Areas" section
> that does something similar for child area notes. Area notes can only be children of
> other area notes or `~/bob/area.md`, so those are the only files where the section
> should appear. Lead the design so it is intuitive, reliable, and beautiful; critique the
> plan, adjust the requirements where justified (calling each adjustment out), and end
> with a recommended solution.
>
> **Researcher:** cld · **Date:** 2026-11-14 · **Repos read:** bob-cli (`master` @
> `1a32cc1a`), bob-plugins (linked, `origin/master`), the live `~/bob` vault (read-only).

## Bottom line

**Build it. It is a good idea, and it costs little because the engine already exists.**
Every structural child kind in Bob already gets a generated catalog in its parent
(`## Notebooks`, `## Albums`, `## Projects`). Areas are the only kind with no catalog.
That leaves the area tree navigable only upward, through `parent:`. `area.md` is a dead
end that names one area in prose. `inbox.md` keeps a hand-written list of its child
inboxes, which will drift out of date.

Recommended shape, in one paragraph: a new bob-owned `> [!areas]` callout under an
authored `## Areas` heading. It goes in every area note with at least one child area,
and in the root note that `[[area]]` resolves to (`area.md`). It lists **direct children
only**, A–Z, as `**[[stem]]** — summary`. Rows use the same grammar and the same
shared host-catalog engine as Projects. A new `bob areas list | sync` pair keeps it up
to date, plus a nightly `areas` step. Raw Markdown stays calm and has no counts. All
visual polish lives in an Obsidian card: hue dots, `● today`, project counts, and
`▸ N` expanders.

Adjustments I recommend (details in [Adjustments](#adjustments-to-the-requirements)):

| # | Adjustment | Why |
| --- | --- | --- |
| **A1** | A new optional `summary:` key on area notes feeds the row tail | No existing area text can serve as a description; first paragraphs are boilerplate, task lines, or badge rows |
| **A2** | Every area appears in **exactly one** Areas catalog. Areas with a missing or invalid `parent` are listed in `area.md` with ⚠️ | Your "can only be children of areas or `area.md`" rule is enforced nowhere today. This makes it visible and keeps the root map complete |
| **A3** | `## Areas` sits **above** `## Projects`. The first write of either catalog keeps that order, whichever comes first | Areas contain projects, so broad comes before narrow. Without this, catalog order depends on which one was created first |
| **A4** | New CLI noun `bob areas list | sync` plus a nightly step, rather than folding into `bob projects sync` | Areas have no lifecycle, and the CLI rules say to nest only under a noun with a stated membership rule |
| **A5** | Bob also *removes* a stray `[!areas]` region from any area or project note that has no child areas | A note whose type changed from area to project must not keep a stale list forever |
| **A6** | Live counts and hues go **only** in the plugin card, never in stored Markdown | Otherwise one child's task edit would rewrite its parent note. The Notebooks contract already says "hue, counts, and age are drawn by clients" |

## Contents

- [What exists today](#what-exists-today)
- [Is this a good idea? A critique](#is-this-a-good-idea-a-critique)
- [Approaches considered](#approaches-considered)
- [Adjustments to the requirements](#adjustments-to-the-requirements)
- [Recommended design](#recommended-design)
  - [Markdown contract](#1-markdown-contract-what-bob-writes)
  - [CLI: `bob areas`](#2-cli-bob-areas-list--sync)
  - [bob-cli integration points](#3-bob-cli-integration-points)
  - [The Obsidian card](#4-the-obsidian-areas-card-the-beautiful-part)
  - [Docs and decision record](#5-docs-and-decision-record)
- [Reliability: invariants and acceptance tests](#reliability-invariants-and-acceptance-tests)
- [Rollout](#rollout)
- [Open questions for Bryan](#open-questions-for-bryan)
- [Recommended solution](#recommended-solution)

## What exists today

### The shared host-catalog engine is already generic

`src/native/host_catalog/region.rs` defines one `RegionSpec` per bob-owned callout kind:

| Spec | Callout | Heading | First-write placement | Malformed opener |
| --- | --- | --- | --- | --- |
| `NOTEBOOKS` (`region.rs:59`) | `[!notebooks]` | `Notebooks` | `BeforeFirstTasks` | lenient (legacy markers) |
| `ALBUMS` (`region.rs:75`) | `[!albums]` | `Albums` | `AfterSectionThenTasks("Notebooks")` | strict |
| `PROJECTS` (`region.rs:87`) | `[!projects]` | `Projects` | `BeforeFirstH2` | strict |

`GENERATED_CATALOGS` (`region.rs:98`) lists every spec. Capture uses it to refuse
section targets (`capture/sections.rs:565`, `:575`), and it keeps generated headings
from being treated as task drawers (`capture_drawers.rs:550`). The engine edits only the
callout, as byte-span replacements. It keeps a BOM and CRLF intact, ignores frontmatter
and fenced examples, removes the callout when the host has no rows, and removes the
heading only when its section is then blank. Bryan owns the heading and its position
after the first write. An `[!areas]` spec is one more constant here.

### How the Projects catalog works (the model to copy)

- **Planner** (`src/native/projects/catalog.rs:163` `plan_catalogs`). This is a pure
  function. Hosts are area and project notes outside `done/` and excluded directories.
  Each child's scalar `parent:` resolves through `NoteIndex`: exact path first, then a
  unique case-insensitive basename. Alias forms such as `[[love.md|love]]` resolve, as
  `project_dependencies/tests.rs:262` checks. Each host lists **direct children only**.
- **Row grammar** (`catalog_rows.rs`): `> - [glyph ]**[[link]]**[ — tail]`. The link is
  the stem, or `path|stem` when the stem is ambiguous. Open rows sort A–Z. Closed rows
  sit under `> - **Closed**`.
- **Commands**: `bob projects list` reports catalog state (`current`, `missing`,
  `stale`, `damaged`). `bob projects sync` installs one combined postimage per note under
  the shared vault lock and makes one scoped commit. `bob nightly` runs `projects`,
  `notebooks`, and `albums` steps (`nightly.rs:30`).
- **Readers**: the PDF note snapshot rewrites `[!projects]` into a linked block
  (`highlights_ref/note_snapshot/bob.rs:335`). The Obsidian **Projects catalog card**
  (`bob-ledger-tools/src/241ac…241ae`, `styles.css` ≈ line 9138) is a display-only view
  of `bob projects list -f json`. It adds hued ring markers, task, `● today`, and
  blocked-reason chips, a folded Closed peek, `▸ N` child expanders, and `↻ sync`,
  Retry, and `＋ project` actions. The callout icon is `lucide-puzzle`. Notebooks use
  `lucide-notebook-tabs` and Albums use `lucide-album`.
- **Earlier decisions** from the sub-projects catalog research
  (`202611/subprojects_catalog_section/subprojects_catalog_section.md`):
  - D7: *direct children only; depth shows in the plugin as a `▸ N` expander, never in
    Markdown*, because a grandchild change must rewrite one parent, not every ancestor.
  - D8: *catalogs read goal → parts → knowledge → work*.

### The vault's area tree today

The vault has 19 area notes, all at the vault root. Each sets a scalar `parent:`. Seven
point at `[[area]]`. This text tree is also the proposed human output of
`bob areas list` (each `●` would print in the area's hue):

```text
area.md                       ← root type note (parent: [[type]]); hosts Areas
├── ● body
├── ● cash                    ← hosts Areas
│   ├── ● bank
│   └── ● recur
├── ● dev
├── ● gtd                     ← hosts Areas (and already hosts Projects)
│   ├── ● gtd_daily
│   └── ● inbox               ← hosts Areas (prose already lists these three by hand)
│       ├── ● gkeep_inbox
│       ├── ● gmail_inbox
│       └── ● mac_inbox
├── ● job
├── ● love                    ← hosts Areas
│   ├── ● abby
│   ├── ● family              (parent: "[[love.md|love]]")
│   ├── ● fun
│   ├── ● kelly
│   └── ● vacation            (parent: "[[love.md|love]]")
└── ● meet
```

So **five notes** would grow an `## Areas` section today: `area.md`, `cash`, `gtd`,
`inbox`, and `love`. The tree is three levels deep. It changes rarely: `bank` and
`family` were the newest areas, created 2026-11-11 and 2026-11-02.

### Gaps this feature closes

1. **No downward navigation.** Children point up through `parent:`. Nothing points down.
   Obsidian's backlinks pane does list child areas, but they are buried among hundreds
   of task-link backlinks. `love.md` alone has dozens of task rows.
2. **`area.md` is a dead end.** Its prose mentions `[[job]]` only as an example. The
   root of the hierarchy can't show you the hierarchy.
3. **Hand-written lists drift.** `inbox.md` says "Root of the inbox files: [[mac_inbox]],
   [[gkeep_inbox]], and [[gmail_inbox]]". That list was written by hand.
4. **Area parents are not validated at all.** The code has no `area_parent_*` finding,
   and nothing checks that an area's parent is an area. Inbox membership
   (`vault-format.md`: "Inbox files are area notes whose `parent` resolves to
   `inbox.md`") and root-parent walks both depend on area parents being right. A typo
   today fails silently.

## Is this a good idea? A critique

**Yes, but not mainly for the reason it first looks.** The visible win is navigation:
`area.md` becomes an atlas and each parent area becomes a hub. The bigger win is
reliability. To render the section, bob must resolve and validate every area's `parent`
for the first time. That turns your rule ("areas can only be children of areas or
`area.md`") from a convention into something bob checks.

What makes it cheap:

- The engine, transaction, lock, commit, nightly, and capture-protection machinery are
  all shared. A new catalog kind is one `RegionSpec`, a small planner, and one CLI noun.
- The area tree changes rarely and is small (19 nodes). Write churn is close to zero:
  adding, removing, or reparenting an area rewrites at most two hosts.
- The conventions match what Bryan already reads in three other catalogs: the bold
  link, the em-dash tail, A–Z order, and "bob owns the callout, you own the heading".

Honest costs and risks:

- **Another command, nightly step, docs page, and card to maintain.** This is real, but
  the surfaces copy existing ones. The marginal design work is small.
- **Staleness window.** Bob has no area-creation flow. Areas are hand-made in Obsidian,
  so a new sub-area shows up in its parent at the next nightly or on demand. The card
  must make staleness visible (`stale catalog · ↻ sync`), just as the Projects card
  does.
- **The first sync could look bare.** No area has a description today, so rows would be
  bare links until summaries exist. [A1](#a1-add-an-optional-summary-key-to-area-notes)
  and the draft summaries below fix this. Without them the feature still works, but it
  loses most of its looks.
- **Scope creep.** It is tempting to nest the whole tree in `area.md` or to write task
  counts into rows. Both conflict with existing decisions (D7, and the Notebooks
  "clients draw counts" contract). Both would create churn. I reject both
  [below](#approaches-considered).

One thing I would **not** do is generalize the rule into "type notes list their
instances". For example, `project.md` would then list 100 projects. Areas are special
because there are few of them, they form a tree, and they have no end state, which is
what makes a permanent map useful.

## Approaches considered

| Approach | Verdict | Reasoning |
| --- | --- | --- |
| **Stored, bob-owned `[!areas]` callout (direct children)** | ✅ **Recommended** | Matches the three existing catalogs. Readable outside Obsidian: git, GitHub, agents, grep, and PDF snapshots. Stored wikilinks are real graph and backlink edges. Deterministic, validated, and almost never churns. |
| Dataview or Bases query in each area note | ❌ | Needs a plugin to render. Agents and the CLI can't see it, git has no history of it, and the PDF snapshot can't render it. You would hand-paste a query into every host. Its output creates no real links. It also breaks with how every other catalog works. |
| Plugin-only virtual section (nothing stored) | ❌ | Same invisibility problem. It also gives up the "hand-written list drifts" fix for every non-Obsidian reader. |
| Put child areas into the existing `## Projects` catalog | ❌ | Areas have no lifecycle. The state glyphs, the Closed group, criteria, and the card's open/blocked/closed tally would all be meaningless or wrong for them. The heading would stop meaning what it says. |
| Store the **full nested tree** in `area.md` (an "atlas") and direct children elsewhere | ❌ (for stored text) | Breaks D7's rule that one change rewrites one parent. Adding a grandchild would rewrite `area.md` too. It also puts a special case into the contract. The card's `▸ N` expanders and the `bob areas list` tree give the same view without the churn. |
| Hue emoji in stored rows (🟡 love, 🔵 dev …) | ❌ | The emoji set has no aqua or magenta, and violet and magenta would collide. Recoloring an area would rewrite its parent. Notebooks already state that hue is drawn by clients. |
| A generated Mermaid graph of the area tree in `area.md` | ❌ | Pretty but brittle. Links are not real wikilinks, the stored block churns, and it is hard to read on mobile. |
| Fold area sync into `bob projects sync` | ❌ | Mixes two nouns. Projects sync is about lifecycles. The CLI rules say "nest only under a noun with a stated membership rule". |

## Adjustments to the requirements

Each item below changes or extends what was asked. Each is independent, so you can
accept or reject them one by one.

### A1. Add an optional `summary:` key to area notes

**Change:** area notes may declare a one-line `summary:` (≤ 140 characters). The
catalog renders it as the row tail: `**[[love]]** — Kelly, Abby, family, and fun.`

**Why:** The Projects row tail comes from the `^prj` criterion, and areas have none.
Deriving text from the note body does not work. Here is the first prose line of each
area today:

- boilerplate: "[[project]]s / [[area]]s that relate to GTD should link to this note…"
- a task line (`recur`)
- a badge row (`gtd_daily`)
- nothing at all (`gmail_inbox`)

Notebooks already solved this with `summary:`, so reuse that contract: one plain line,
written as inert text, with `_long` and `_multiline` soft findings. Unlike notebooks,
**a missing summary is not a finding**. Areas are fine without one, and 19 day-one
warnings would be noise. The card offers **add summary** on rows that lack one,
reusing the Notebooks affordance.

Draft summaries to start from. Most are lifted from each note's own first line. Rows
marked † are my guesses from the note's name or children. Edit freely.

| Area | Draft `summary:` |
| --- | --- |
| body | Taking care of my body. |
| cash | Money: accounts, bills, and balances. † |
| bank | Every transaction and deposit in our accounts, filed weekly. |
| recur | Recurring money chores. † |
| dev | Open-source and personal software development. |
| gtd | My GTD habits, reviews, and inboxes. |
| gtd_daily | Daily GTD routines. † |
| inbox | New tasks awaiting triage. |
| mac_inbox | Default destination for bob capture and Bob Mac Capture. |
| gmail_inbox | Tasks saved from Gmail. † |
| gkeep_inbox | Tasks drained from Google Keep. † |
| job | My job searches. |
| love | The all-powerful force of LOVE. |
| abby | Being a good dad to Abby. |
| family | Family other than Kelly and Abby. |
| fun | All of the fun stuff in life. |
| kelly | Tasks and notes about Kelly. |
| vacation | Family vacations. |
| meet | Meetings, appointments, and calls. |

### A2. Every area appears in exactly one Areas catalog

**Change:** an area whose `parent` is valid and resolves to an area appears in that
area's catalog. One that resolves to the root appears in `area.md`. Every other area is
listed in **`area.md` as a ⚠️ warning row** with a short reason, and is also reported as
a finding. The other cases are:

- no `parent`
- an unresolvable `parent`
- an ambiguous `parent`
- several `parent` values
- a self-parent
- a cycle
- a parent that is a project, notebook, or other non-area note

**Why:** You stated that "area notes can only be children of other area notes or
`area.md`". Today nothing enforces that, and an invalid parent makes an area silently
invisible. With A2, the root map is always complete and every modeling mistake shows up
in the one place you'd look. Projects already have a ⚠️ row state ("no valid `^prj`
task"), so the vocabulary is familiar.

**If you prefer the strict alternative,** drop invalid areas from all catalogs and rely
only on `bob areas list` findings plus the card's health line. It is simpler, but a
broken area becomes hard to notice.

### A3. `## Areas` sits above `## Projects`, whichever is written first

**Change:** the Areas first write uses the existing `BeforeFirstH2` placement. The
Projects first write changes from `BeforeFirstH2` to a new
`AfterSectionThenFirstH2("Areas")`. That means "after the `## Areas` section if one
exists, else before the first H2". It mirrors the existing `AfterSectionThenTasks`
variant (`region.rs:701`) and is about 10 lines.

**Why:** Order should follow scope, from broad to narrow. Areas, which can contain
projects, come before Projects (finite work), then Notebooks (knowledge), Albums
(records), and Tasks (work). This extends D8's "goal → parts → knowledge → work". The
case to fix: if both specs kept `BeforeFirstH2`, a host that gained its first project
*after* its first sub-area would get `## Projects` inserted *above* `## Areas`. The order
would then depend on history. The rule only governs first writes; after that the
position is yours, as with every catalog. Capture's project creation uses the same
`PROJECTS` spec, so it picks up the new rule for free.

### A4. A new `bob areas` noun with `list` and `sync`, plus a nightly step

**Change:** `bob areas list [-b DIR] [-f human|json]` (read-only) and
`bob areas sync [-b DIR] [-d] [-f human|json]`. Add a nightly step `areas` that runs
before `projects`, so the steps follow the on-page order. The commit subject is
`areas: sync catalogs (N notes)`.

**Why:** You only asked for rendering, but rendering needs an owner. The CLI rules
require a noun with a stated membership rule. Here the rule is "notes whose
frontmatter `type` is `[[area]]`". `list` also gives the plugin card its data source,
and gives you a terminal view of the tree.

### A5. Stray `[!areas]` regions are cleaned up in any area or project note

**Change:** the planner considers every area note, every project note, and the root
when the note has child areas **or already contains an `[!areas]` region**. A host
with no rows gets its callout removed, and its heading too if the section is then blank.
This applies to projects, which can never host areas.

**Why:** If you convert an area into a project, or delete its last sub-area, the old
list must not linger. Notes that are not areas or projects (daily notes, refs, and so
on) are never touched, which matches the Notebooks rule "only host-graph notes are
planned".

### A6. Counts and hues are drawn, never stored

**Change:** stored rows hold only the structure (link, summary, ⚠️ reason). Live
signals belong to the card: hue, `● today`, project and task counts, and child counts.

**Why:** This keeps D7's "one change rewrites one parent". A task edit in `kelly.md`
must never rewrite `love.md`. It also follows the Notebooks contract ("No colors,
counts, recency… are written; hue, counts, and age are drawn by clients"). The
`## Tasks` badge row is a stored count, but it is fine because it counts tasks in its
own note.

## Recommended design

### 1. Markdown contract (what bob writes)

**Spec**

```rust
/// The child-area catalog spec: `[!areas]`, `## Areas`, before the first H2 on
/// its first write, with strict malformed-opener handling.
pub(crate) const AREAS: RegionSpec<'static> = RegionSpec {
    callout: "areas",
    heading: "Areas",
    head_title: None,
    placement: Placement::BeforeFirstH2,
    legacy: None,
    strict_bare: true,
};
// GENERATED_CATALOGS = &[AREAS, NOTEBOOKS, ALBUMS, PROJECTS];
// PROJECTS.placement = Placement::AfterSectionThenFirstH2("Areas");   // A3
```

**Rules**

- **Root.** The root is the note that the bare link `[[area]]` resolves to through
  `NoteIndex` (today `area.md`), outside `done/` and excluded directories. No
  frontmatter is required on it. If nothing resolves, there is no root host and bob
  reports `areas_root_missing`.
- **Hosts.** A host is the root, or any area note outside `done/` and excluded
  directories with at least one row. Under A5, any area or project note that already
  has an `[!areas]` region is also planned, so the region can be removed.
- **Membership.** Each area's scalar `parent:` resolves with the same resolver Projects
  uses (`resolve_project_parent`): exact path, then a unique case-insensitive basename,
  with alias, path, and heading forms accepted. A parent that is an area or the root
  puts a plain row in that host. Every other outcome puts a ⚠️ row in the root (A2).
  **Direct children only, no rollup.**
- **Row grammar**, a subset of the Projects grammar, so `parse_row` reuses unchanged:
  - `> - **[[stem]]**[ — summary]`
  - `> - ⚠️ **[[stem]]** — reason`
  - The link is the stem, or `path-without-md|stem` when the stem alone is ambiguous
    (`link_inner`, `catalog.rs`).
  - The summary is inert text, escaped with `notebooks::catalog::inert_text`.
  - Reasons are bob-authored and fixed: `no \`parent\``, `\`parent\` not found`,
    `\`parent\` is ambiguous`, `several \`parent\` values`, `\`parent\` is itself`,
    `\`parent\` cycle`, `\`parent\` is not an area`.
- **Order.** A–Z by stem, case-insensitive, with the path as tiebreaker. ⚠️ rows sort
  inline like Projects warning rows, so the glyph does the attention work. Areas have
  no Closed group.
- **Ownership, damage, and states** are identical to Projects:
  - Bob owns only the callout.
  - A malformed `> [!areas` opener makes the host `areas_catalog_damaged`. The host is
    left untouched and the command exits 1, while healthy hosts still apply.
  - Duplicate well-formed callouts self-heal by keeping the first.
  - States are `current`, `missing`, `stale`, and `damaged`.
- **Empty host.** Bob deletes the callout. It deletes `## Areas` only if the section is
  then blank, so authored prose keeps the heading.

**What it looks like.** These are the predicted first-sync results on today's vault,
with the A1 summaries filled in.

`area.md` has no H2, so the block lands at EOF after one blank line:

```markdown
---
parent: "[[type]]"
created: 2026-06-11 17:04
---

Area notes link to this note as their `type`.

Use this type for ongoing spheres of responsibility with no end state, such as [[job]]. …

## Areas

> [!areas]
>
> - **[[body]]** — Taking care of my body.
> - **[[cash]]** — Money: accounts, bills, and balances.
> - **[[dev]]** — Open-source and personal software development.
> - **[[gtd]]** — My GTD habits, reviews, and inboxes.
> - **[[job]]** — My job searches.
> - **[[love]]** — The all-powerful force of LOVE.
> - **[[meet]]** — Meetings, appointments, and calls.
```

If an area named `sleep` had `parent: "[[body_habits]]"` and that note were a project,
the root would also show:

```markdown
> - ⚠️ **[[sleep]]** — `parent` is not an area
```

`gtd.md` gets its first H2 before the existing `## Projects` (A3):

```markdown
[[project]]s / [[area]]s that relate to GTD should link to this note file as their `parent`.

Related: [[prj_gtd]] [[now_gtd]] [[project_checklists]] [[gtd_ref]] [[pomodoro]] [[legacy_gtd]]

## Areas

> [!areas]
>
> - **[[gtd_daily]]** — Daily GTD routines.
> - **[[inbox]]** — New tasks awaiting triage.

## Projects

> [!projects]
>
> - **[[needs_attn_tasks]]** — Review all of the tasks in the needs_attn_tasks file!
```

`love.md` gets it before `## Notebooks`:

```markdown
## Areas

> [!areas]
>
> - **[[abby]]** — Being a good dad to Abby.
> - **[[family]]** — Family other than Kelly and Abby.
> - **[[fun]]** — All of the fun stuff in life.
> - **[[kelly]]** — Tasks and notes about Kelly.
> - **[[vacation]]** — Family vacations.

## Notebooks
```

Once this lands, the hand-written child list in `inbox.md`'s first line becomes
redundant. Bob never edits authored prose, so pruning it is Bryan's call. The same goes
for `area.md`'s line about sub-areas.

### 2. CLI: `bob areas list | sync`

Add it to the **Vault** help section, in alphabetical order:
`albums, areas, articles, …`. Every long option gets a short alias, per the CLI rules.

**`bob areas list`** is read-only and prints the colored tree shown
[above](#the-vaults-area-tree-today):

- Each `●` prints in the area's hue.
- The summary prints dim after the name.
- Right-aligned quiet columns show `N projects` (open direct-child projects) and
  `● today`.
- A one-line repair footer appears when any catalog is `missing` or `stale` (for
  example, `2 catalogs stale · run bob areas sync`).
- Damaged catalogs and parent errors print as findings under their path. A damaged
  catalog exits 1.

`-f json` returns one envelope:

```jsonc
{
  "schema_version": 1, "ok": true, "command": "list", "today": "2026-11-14",
  "root": { "path": "area.md", "stem": "area" },          // null when unresolved
  "areas": [{
    "path": "love.md", "stem": "love", "parent": "area.md", "depth": 1,
    "children": ["abby.md", "family.md", "fun.md", "kelly.md", "vacation.md"],
    "summary": null,
    "issue": null,                                        // or {code, message}
    "projects": { "open": 0, "branch_open": 0 },          // direct / whole branch
    "tasks": { "open": 12, "branch_open": 41, "today": 0, "branch_today": 1 }
  }],
  "catalogs": [{ "host": "love", "path": "love.md", "kind": "area",   // or "root"
                 "state": "current", "rows": { "areas": 5, "warning": 0 }, "issues": [] }],
  "findings": [{ "code": "area_parent_kind", "severity": "warning", "path": "sleep.md",
                 "message": "`parent` [[body_habits]] is a project, not an area" }],
  "counts": { "areas": 19, "catalogs": 5, "errors": 0, "warnings": 0 }
}
```

Field definitions:

- **Branch.** An area's branch is the area plus all its descendant areas, plus the
  projects (and their sub-projects) whose parent is one of those areas.
- **`tasks.today`** has the same meaning as in Projects: an open task in the scope with
  a live Task Link under today's open Pomodoros, read from the ledger as in
  [decision `today-is-read-from-the-ledger`].
- **Findings:**
  - Warnings:
    - parent problems: `area_parent_missing`, `area_parent_unresolved`,
      `area_parent_ambiguous`, `area_parent_list`, `area_parent_self`, `area_cycle`,
      `area_parent_kind`
    - summary problems: `area_summary_long`, `area_summary_multiline`
    - `areas_root_missing`
    - `areas_catalog_stale`
  - Errors: `areas_catalog_damaged`.

**`bob areas sync`** follows the Notebooks and Projects sync contract word for word:

- `-d` prints a colored unified diff per host and writes nothing.
- A real run verifies the vault and pre-syncs. It takes the shared maintenance lock and
  plans from the synced snapshot. It revalidates preimages, installs through the guarded
  writer, and makes one commit. Then it post-syncs.
- A vault with nothing to change writes nothing and commits nothing.
- Damaged hosts are skipped and reported, and the command exits 1.

Reparenting an area updates both the old and the new host in the same commit.

**Nightly:** `vault-sync, task archive, articles, period notes, areas, projects,
notebooks, albums, vault-sync`. The step order matches the on-page section order. The
steps are independent: each plans from the bytes the previous step left.

### 3. bob-cli integration points

| File | Change |
| --- | --- |
| `host_catalog/region.rs` | `AREAS` spec. Add it to `GENERATED_CATALOGS`. New `Placement::AfterSectionThenFirstH2` and the `PROJECTS.placement` change (A3). Re-export from `host_catalog/mod.rs`. |
| new `src/native/areas/` (`mod.rs`, `scan.rs`, `catalog.rs`, `sync.rs`, `output.rs`) | A pure planner modeled on `projects::catalog::plan_catalogs` (root detection, membership, A2 orphan routing, row rendering through the shared `render_row` or a sibling). Plus `list` and `sync` on the shared `host_catalog::txn`. Reuse `projects::catalog_rows::parse_row` for reading. |
| `nightly.rs` | An `areas` step before `projects`. Update the help blurb. |
| `capture/sections.rs` (`reject_generated_catalog_selector`) | Add the triple `(AREAS, "\`## Areas\` is the generated child-area catalog (written by \`bob areas sync\`)…", "areas_section_generated")`, so `@love#areas` refuses instead of writing into or above the callout. |
| `capture_drawers.rs`, `task_merge` | Covered by `GENERATED_CATALOGS`. Extend the `["Notebooks", "Albums", "Projects"]` test loop at `task_merge/tests.rs:769`. |
| `highlights_ref/note_snapshot/bob.rs:335` | Optional: map `[!areas]` like `[!projects]`, turning it into a linked block and ⚠️ into a `needs parent` chip. Without this it renders as a plain callout, which is acceptable for v1. |
| CLI registration and completion | New `areas` noun in the Vault section, plus completions. Then run `just docs-gen`. |

### 4. The Obsidian Areas card (the beautiful part)

The card is a sibling of the Projects card in `bob-ledger-tools`, built on the same
helpers: `albumReplaceChrome`, `notebookBindAction`, fold maps, the stale and Retry
model, and the container-query breakpoints. Like the Projects card, it is **display
only**: membership and order come from the stored rows and from `bob areas list -f json`.
It never re-resolves parents in JavaScript and never edits catalog text.

```text
area.md ─────────────────────────────────────────────────────────────
╭─ ◎ Areas ───────────────────────────── 7 areas · ● 2 today ─╮
│  ● body     Taking care of my body.                           │   ● green
│  ● cash     Money: accounts, bills, and balances.      ▸ 2    │   ● magenta
│  ● dev      Open-source and personal software…  3 projects    │   ● blue
│  ● gtd      My GTD habits, reviews, and inboxes.               │   ● grey
│             ● today · 1 project                        ▾ 2    │
│     ┊ ● gtd_daily                                              │
│     ┊ ● inbox                                         ▸ 3     │
│  ● job      My job searches.                    1 project      │   ● aqua
│  ● love     The all-powerful force of LOVE.            ▸ 5    │   ● yellow
│  ● meet     Meetings, appointments, and calls.  ● today       │   ● violet
╰───────────────────────────────────────────────────────────────╯
```

Design choices, each tied to what already exists:

- **The marker means something.** A Projects row has a **ring**, because a project can
  be finished. An Areas row has a **solid dot**, because an area is never finished.
  Each dot is painted in that child area's hue, using the same shared resolver that
  paints home chips and the Projects card (`pomodoroHomeResolve`), so colors always
  agree. In `area.md` this gives a rainbow of the top-level areas. In `love.md` every
  child inherits yellow. To keep hue ownership readable, an area with its own `color:`
  gets a full-strength dot and an inherited hue gets a softer tint (about 45%).
- **The card tint** follows the host's hue, as in the Projects card (`data-root-hue`).
  `area.md` has no hue, so its card stays neutral and the row dots carry the color.
  That is the right look for a root.
- **The icon** is `--callout-icon: lucide-orbit`. It suggests something ongoing and
  cyclical with no end state, and it is distinct from puzzle, notebook-tabs, and album.
- **Calm chips**, at most three per row:
  - `● today` (accent color) when the branch has a live Task Link today.
  - `N projects` (muted, hidden at 0) for open projects in the branch.
  - `▸ N` to expand child areas inline. Expanded children render as mini rows with
    their own dots, recursively. Shift-click expands the whole branch.

  Task counts stay **out of the row** and go in the dot's tooltip, for example
  `love · yellow · 41 open tasks in the branch (12 here, 29 in 5 sub-areas)`. An area
  catalog is a map, not a to-do list. A count of 24 blocked tasks in `love` is not
  something you act on from its parent.
- **Header and health.** The header shows a tally (`7 areas · ● 2 today`). A stale or
  missing catalog shows `stale catalog · ↻ sync`, which runs `bob areas sync`. A failed
  report fetch shows **Retry** and keeps the last good rows. ⚠️ rows show their reason
  in the warning color with a tooltip naming the fix ("set `parent:` to an area or
  `[[area]]`"). Rows without a summary get a quiet **add summary** action that opens
  Properties at `summary`, reusing the Notebooks code path.
- **Folds** stay local to each pane and are collapsed by default. At narrow widths
  (`@container … max-width: 440px`), chips wrap below the summary, as on the Projects
  card.
- **There is no `＋ area` action.** Bob has no area-creation flow, and a clipboard
  starter that can't create an area would be a false promise. If an area-capture form
  is ever added, the slot is ready.

### 5. Docs and decision record

Per the docs memory routing:

- **Contract:** a new root page `docs/areas.md` ("Area catalogs"). It covers hosts,
  membership, the A2 routing, row grammar, order, placement, ownership, damage, states,
  `list`, `sync`, JSON, and nightly.
- **Reference:** `docs/reference/cli/areas.md` via `just docs-gen`.
- **Format:** `docs/reference/vault-format.md` § Area notes gains `summary:` and an
  `## Areas` example.
- **Cross-references:**
  - `docs/projects.md` § Projects catalogs gets a one-line note on the A3 placement.
  - `docs/notebooks.md` § Section protection gets the `areas_section_generated` line.
  - bob-plugins `docs/bob-ledger-tools.md` gains an "Areas catalog card" section.
- **Glossary:** the *Area Note* strand should mention the `## Areas` catalog and
  `summary:`. That is a memory change, so it goes through `/sase_memory_write` or a
  memory task bead. It is not part of this research.
- **Decision record** (proposed, for Bryan to accept):
  - Title: *"Every Area Appears In Exactly One Areas Catalog"*.
  - Claim: direct children only; invalid parents route to the root with ⚠️; counts and
    hue are drawn by clients.
  - Rejected alternatives: a nested atlas, Dataview, and merging into Projects.
  - Reopens if areas gain a lifecycle or multiple parents.

## Reliability: invariants and acceptance tests

Invariants:

1. **Each area appears in exactly one catalog** whenever a root exists (A2).
2. **One change rewrites at most two hosts**: the old parent and the new parent on a
   reparent, otherwise one. Task edits never rewrite a catalog (A6).
3. **Idempotent:** a second `sync` is a no-op with no commit.
4. **Bob writes only the callout bytes**, except on the first write, which adds the
   heading, and on removal, which deletes a heading whose section is blank. A BOM, CRLF,
   frontmatter, and fenced examples are preserved.
5. **Catalog order is deterministic**, Areas before Projects, whatever the creation
   history (A3).

Acceptance tests:

| # | Scenario | Expectation |
| --- | --- | --- |
| 1 | Fixture mirroring today's tree (19 areas) | Exactly 5 hosts with the golden bytes shown above. `area.md` gets the block at EOF. |
| 2 | Run `sync` twice | The second run reports `current` everywhere and makes no commit. |
| 3 | Reparent `kelly` from `love` to `family` | `love` loses the row and `family` gains a catalog, in one commit. |
| 4 | Parent missing, unresolved, ambiguous, list-form, self, cycle, or project/notebook | A ⚠️ row in the root with the exact reason text, plus the matching finding. No row anywhere else. |
| 5 | No `area.md` | `areas_root_missing`. Top-level and orphan areas are listed nowhere. Healthy area hosts still sync. |
| 6 | Sub-area added before a first project, and the reverse | `## Areas` sits above `## Projects` in both orders. |
| 7 | Last child removed, with and without prose under `## Areas` | The callout is removed. The heading is removed only when its section is blank. |
| 8 | Malformed `> [!areas` opener | Host untouched, `areas_catalog_damaged`, exit 1. Other hosts apply. |
| 9 | A project note carrying a stale `[!areas]` region | The region is removed (A5). |
| 10 | `bob capture '@love#areas' 'x'` | Refuses with `areas_section_generated`. |
| 11 | `parent: "[[love.md|love]]"` and `"[[dir/x|X]]"` | Both resolve as membership. |
| 12 | A summary containing `[[x]]`, `#tag`, `**`, or a newline | Inert escaping. A newline raises `area_summary_multiline`. |
| 13 | An area under `done/`, `_templates/`, or `.obsidian/` | Neither host nor child. |
| 14 | CRLF and BOM host | Byte-identical outside the callout. |

## Rollout

1. **bob-cli, one PR.**
   - Add the `AREAS` spec, the planner, `bob areas list | sync`, and the nightly step.
   - Add capture protection and the A3 placement change.
   - Write the docs (`docs/areas.md`, vault-format, CLI reference).
   - Add the tests above.
   - It ships on the daily release train as additive CLI.
   - Then run `bob areas sync -d` on the real vault and check the five diffs.
2. **Vault.** Bryan adds `summary:` values (the drafts above are a starting point), runs
   `bob areas sync`, and optionally prunes the now-redundant prose in `inbox.md` and
   `area.md`.
3. **bob-plugins.** Build the Areas card (model, DOM, and plugin fragments plus CSS) and
   the docs section. Run `npm run build` and `npm test`, then `bob plugins sync`.
4. **Follow-ups (optional).**
   - The note-snapshot mapping for PDFs.
   - Surface area `summary` in `capture-targets` JSON, so Mac Capture route completions
     show what `@love` means.
   - The decision record and the glossary strand update.

## Open questions for Bryan

1. **Orphan routing (A2):** list invalid areas in `area.md` with ⚠️ (recommended), or
   drop them and rely on findings only?
2. **Order (A3):** Areas above Projects (recommended), or Projects first because
   projects are more actionable? Either way, the first-write rule should pin one order.
3. **Summaries (A1):** are you happy adding `summary:` to area notes? Do the drafts read
   right?
4. **Card density:** should an open-task count chip be visible on rows, or kept in the
   tooltip (recommended)?

## Recommended solution

Add a bob-owned **`> [!areas]` catalog under `## Areas`**:

- **Where it appears:** every area note with child areas, and the root note that
  `[[area]]` resolves to (`area.md`). Today that is five notes: `area.md`, `cash`,
  `gtd`, `inbox`, and `love`.
- **What it lists:** **direct children only**, A–Z, as `**[[stem]]** — summary`. The
  summary comes from a new optional `summary:` key (A1). Every area is listed exactly
  once: an area with an invalid `parent` appears in `area.md` as a ⚠️ row with a reason
  (A2), which finally enforces your rule that areas belong only under areas or
  `area.md`.
- **Engine:** the existing host-catalog engine, with a new `AREAS` `RegionSpec` and the
  same ownership, damage, and state rules as Projects.
- **Position:** first-write placement keeps **Areas above Projects** whichever is
  created first (A3). After that, the position is yours.
- **Maintenance:** a new **`bob areas list | sync`** noun (A4). `list` prints a colored
  tree and is the card's JSON source. `sync` does one guarded commit. A nightly `areas`
  step runs before `projects`. Stray regions are cleaned up (A5).
- **Capture:** `@x#areas` is refused like the other generated catalogs.
- **Stored Markdown:** structural only (A6).
- **The beauty lives in the Obsidian card:** solid hue dots (rings are for projects,
  dots are for areas), a neutral root card with a rainbow of area hues, a `lucide-orbit`
  icon, calm `● today` and `N projects` chips, `▸ N` expanders that show the whole tree
  on demand, add-summary prompts, and `↻ sync` when the catalog is stale.

[decision `today-is-read-from-the-ledger`]: https://bobs-org.github.io/develop/decisions/#today-is-read-from-the-ledger
