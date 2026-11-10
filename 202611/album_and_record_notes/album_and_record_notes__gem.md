# Architectural Research: Album Notes, Record Notes, and Root-Parent Area Lineage

**Author:** Researcher `gem` (5-Researcher Swarm)  
**Date:** 2026-11-10  
**Target Architecture:** Bob Vault & `bob-cli` Record System  
**Status:** Complete Proposal & Comparative Analysis

---

## 1. Executive Summary

This report investigates the architecture for integrating **Record Notes** (e.g., individual restaurant, podcast, TV show, and movie files) into Bob's hierarchical network of **Area Notes** by introducing **Album Notes** (`type: "[[album]]"`).

Historically in Bob, tasks, projects, and notebooks maintain strict parentage chains that terminate at an Area of Responsibility (`type: "[[area]]"`), establishing an unambiguous **root parent** for metrics, Pomodoro time attribution, and GTD reviews. In contrast, record notes have existed in semi-isolated silos: each record note in `<dir>/` points to its collection note (`parent: "[[<dir>]]"`), but collection notes like `eat.md` and `podcasts.md` lacked a typed role in Bob's ontology, lacked parent links to life areas, contained legacy Zorg-era formatting, and drew their schema from machine-local configuration files (`~/.config/bob/config.yml`).

### Core Recommendations

1. **Adopt "Album Notes" (`type: "[[album]]"`)**: Standardize collection root notes (`eat.md`, `podcasts.md`, `tv.md`, `movies.md`) as Album Notes. Each album note owns exactly one eponymous subfolder (`eat/`, `podcasts/`, `tv/`, `movies/`) and names an ongoing Area Note as its `parent:` (e.g., `eat.md` -> `[[body]]`, `podcasts.md` -> `[[dev]]`, `tv.md` -> `[[fun]]`). This gives every record note a continuous, unbroken path to a root Area of Responsibility.
2. **Migrate Record Schemas to Album Frontmatter**: Relocate the `records:` configuration block from `config.yml` into a dedicated `record:` mapping within each Album Note's YAML frontmatter. This turns the vault into a self-contained, multi-machine source of truth, removing configuration drift across Athena, Apollo, and MacBook hosts.
3. **Dezorg Album Notes via Legacy Notebooks**: Follow the proven pattern established during the dezorging of `job.md`: extract all unstructured Zorg tables, raw LID markers, and legacy notes into companion notebooks (e.g., `legacy_eat.md`, `type: "[[notebook]]"`, `parent: "[[eat]]"`), leaving the album note pristine and focused.
4. **Deploy a Hybrid Summary in Album Notes**: Combine high-visibility status filter chips (`[ 🍽️ 105 total ] · [ 💚 42 liked ] ...`) and a compact summary callout (`> [!summary]`) with an embedded Obsidian Base (`![[<album>.base]]`). This delivers instant terminal/GitHub readability alongside Obsidian's interactive table/kanban capabilities without causing severe git-diff churn.
5. **Catalog Albums in Parent Area Notes (`## Albums`)**: Introduce a machine-managed `## Albums` section in Area Notes (analogous to the existing `## Notebooks` catalog managed by `bob notebooks sync`). Parent areas will display a compact, informative callout (`> [!albums]`) showing child albums, record counts, and status breakdowns.
6. **Formulate Canonical Glossary Entries**: Add formal definitions for `album-note.md` and `record-note.md` to Bob's SASE reference memory web (`sase/memory/glossary/`).

---

## 2. Problem Analysis & Current State Critique

### 2.1 The Disconnected Lineage Gap

In Bob's information architecture, everything a user does or tracks should roll up to a fundamental life area:

```
[area: body] <--- [album: eat] <--- [record: burger_bistro]
[area: dev]  <--- [album: podcasts] <--- [record: python_bytes]
[area: fun]  <--- [album: tv] <--- [record: severance]
```

Currently, this hierarchy breaks at the collection note boundary:
- **`~/bob/eat/burger_bistro.md`** has `parent: "[[eat]]"` and `type: "[[restaurant]]"`.
- **`~/bob/eat.md`**, however, has `parent: [[h2_role]]` (an obsolete Zorg artifact) and no `type:` declared. It is completely disconnected from `body.md`.
- **`~/bob/podcasts.md`** has `parent: "[[mind]]"`, missing the direct link to developer responsibilities (`[[dev]]`), and lacks a formal `type:`.
- **`~/bob/tv.md`** has `parent: "[[fun.md|fun]]"`, lacking standard unquoted wikilink normalization and type declarations.

Because collection notes do not resolve to a valid Area, record notes cannot resolve a `root_parent`. If Pomodoro time is logged while reviewing restaurants or listening to podcasts, or if statistics are calculated on vault entities, these records float in an unattached `@unfiled` limbo.

### 2.2 Machine-Local Configuration vs. Vault Portability

Currently, record types are defined in `~/.config/bob/config.yml`:

```yaml
records:
  restaurant:
    dir: eat
    label: Restaurant
    emoji: 🍽️
    dated_notes: true
    fields:
      status: { required: true, values: { to_try: 🔖 To try, liked: 💚 Liked, not_liked: 🚫 Not liked } }
      category: { required: true, suggest: true }
      location: { required: true, suggest: true }
      ...
```

This architecture has major limitations:
1. **Multi-Host Configuration Drift**: Bryan operates across multiple machines (`athena`, `apollo`, `mac`). If a schema field or choice is updated in `config.yml` on the Mac, running `bob records check` or capturing on Athena fails until dotfiles are synchronized.
2. **Decoupled Architecture**: The data lives in `~/bob/eat/`, the dashboard lives in `~/bob/eat.md`, but the schema rules governing them live in `~/.config/bob/config.yml`.
3. **Friction in Creating New Collections**: Adding a collection (e.g., board games, coffee beans, books) requires editing an external dotfile rather than simply creating a note in Obsidian.

### 2.3 The Duality of Type Notes vs. Collection Notes

An inspection of `~/bob/` reveals an awkward duality:
- `~/bob/podcast.md`: Scaffolded on Nov 9 as an inert "Type Note" (`parent: "[[type]]"`, 9 lines).
- `~/bob/podcasts.md`: The active collection note (`parent: "[[mind]]"`, 50 lines, contains lists of subscribed/unsubscribed podcasts and links to `podcasts.base`).
- For restaurants: The collection is `eat.md` (folder `eat/`), but the record type is `restaurant` (type note `restaurant.md`).

This duality creates confusion about which note is the collection and which note is the type. Migrating to Album Notes resolves this cleanly: the album note *is* the collection note and the authoritative owner of the record type schema.

---

## 3. Architectural Critique: Is This a Good Idea?

### 3.1 Philosophical Assessment: An Area-Rooted Vault

**Verdict: Emphatically YES.**

In personal knowledge management and GTD systems, orphaned tracking silos inevitably decay into digital clutter. When a tracker (e.g., dining, media consumption, podcasts) is unanchored from an ongoing sphere of responsibility:
- It receives no routine review during GTD horizon checks.
- It cannot inform area-level dashboards or period summaries.
- It fragments search and navigation.

By formally anchoring `eat.md` under `body.md`, `podcasts.md` under `dev.md`, and media under `fun.md`, Bob establishes a complete **4-Tier Entity Ontology**:

| Dimension | GTD Action Hierarchy | Knowledge / Thinking Hierarchy | Structured Entity Hierarchy |
| :--- | :--- | :--- | :--- |
| **Container (Root)** | **Area Note** (`type: "[[area]]"`) | **Area Note** (`type: "[[area]]"`) | **Area Note** (`type: "[[area]]"`) |
| **Middle Tier** | **Project Note** (`type: "[[project]]"`) | **Notebook Note** (`type: "[[notebook]]"`) | **Album Note** (`type: "[[album]]"`) |
| **Unit Tier** | **Task** (`- [ ] #task`) | **Note Bullet** (`- Note text ^id`) | **Record Note** (`type: "[[<kind>]]"`) |

This symmetry is elegant, intuitive, and natural.

### 3.2 Critique of Moving Schemas into Album Frontmatter

Migrating schemas from `config.yml` to Markdown frontmatter is a substantial shift. Here is a balanced critique:

#### Advantages
- **Vault Portability**: The vault becomes entirely self-describing. Any machine that clones the vault immediately has the full record schemas without installing dotfile updates.
- **Co-location of Concerns**: The album note houses the schema, the collection summary, and the link to the parent area.
- **Natural Extensibility**: Creating a new album is as easy as running `bob albums new books -p mind` or creating `books.md` in Obsidian with a `record:` block.

#### Risks & Mitigations
- **Risk 1: Capture Latency & Parsing Overhead**: If `bob capture` has to parse YAML frontmatters across the vault to discover schemas before saving `@eat/` records, capture could slow down.
  - *Mitigation*: Album notes live strictly at the vault root (`~/bob/*.md`). Scanning root-level markdown frontmatters takes <3ms. Furthermore, Bob can maintain a lightweight cache in `.bob/cache/albums.json` that revalidates using file modification timestamps (`mtime`).
- **Risk 2: YAML Syntax Errors in User-Edited Markdown**: A typo made while hand-editing an album note in Obsidian could invalidate the schema.
  - *Mitigation*: The CLI command `bob records check` (or `bob albums check`) will strictly lint album frontmatters, emitting typed diagnostics with exact line numbers and helpful error messages.

---

## 4. Detailed Design: The Album Note (`type: "[[album]]"`)

### 4.1 Invariants and Structural Rules

1. **Vault Root Residence**: Album notes MUST reside at the vault root (e.g., `eat.md`, `podcasts.md`, `tv.md`, `movies.md`). They never live in subfolders.
2. **Directory Ownership**: An album note named `<stem>.md` strictly and exclusively owns the record directory `<stem>/`. All record notes belonging to the album reside in `<stem>/<record_stem>.md`.
3. **Single Parent Requirement**: An album note MUST declare exactly one `parent: "[[<area>]]"` pointing to an Area Note (or, in rare cases, a top-level Project Note). Cyclic parentage is prohibited.
4. **No Tasks Permitted**: An album note represents a collection of entities; it is NOT a task residence. It must never contain `- [ ] #task` checkboxes. Actionable work regarding an album belongs in the parent Area note or in a dedicated Project note.
5. **Frontmatter Schema Block**: The album note frontmatter MUST contain a `record:` mapping defining the schema for its member records.

### 4.2 Frontmatter Specification

```yaml
---
parent: "[[body]]"
type: "[[album]]"
record:
  type: restaurant
  label: Restaurant
  emoji: 🍽️
  dated_notes: true
  fields:
    status:
      required: true
      values:
        to_try: 🔖 To try
        liked: 💚 Liked
        not_liked: 🚫 Not liked
    category:
      required: true
      suggest: true
    location:
      required: true
      suggest: true
    companions:
      values: link
      list: true
      default: ["[[kelly]]"]
    visited:
      values: date
    url:
      values: url
  legacy: [lid, source_*]
---
```

### 4.3 Dezorging Album Notes (The `job.md` Pattern)

When `job.md` was recently dezorged, legacy Zorg conversion headers and unstructured content were cleanly separated:
1. All legacy tables and historical notes were relocated into a child notebook: `legacy_job.md` (`type: "[[notebook]]"`, `parent: "[[job]]"`).
2. `job.md` was stripped of `generated_from_zorg`, `zorg_source`, and legacy tags.
3. A clean `## Notebooks` callout was placed in `job.md` linking to `[[legacy_job|Legacy job notes]]`.

Applying this exact procedure to `eat.md`:
- **Create `legacy_eat.md`**:
  ```markdown
  ---
  parent: "[[eat]]"
  created: 2026-11-10T15:00:00-05:00
  type: "[[notebook]]"
  summary: Zorg-era restaurant notes and tables, moved here from eat.md on 2026-11-10.
  ---
  # Legacy restaurant notes

  Contains all historical (Zorg) restaurant tables and notes from [[eat]].

  ## RESTAURANTS LIKED
  ... [legacy table rows] ...

  ## RESTAURANTS NOT LIKED
  ... [legacy table rows] ...
  ```
- **Update `eat.md`**:
  Remove all Zorg headers and tables. Add a `## Notebooks` section:
  ```markdown
  ## Notebooks

  > [!notebooks]
  >
  > - **[[legacy_eat|Legacy restaurant notes]]** — Zorg-era restaurant notes and tables, moved here from eat.md on 2026-11-10.
  ```

---

## 5. Detailed Design: Record Summaries in Album Notes

### 5.1 Evaluation of Summary Formats

| Format | Pros | Cons | Recommendation |
| :--- | :--- | :--- | :--- |
| **A. Static Markdown Table** | Full text in raw markdown; readable in plain editors. | Massive git-diff noise on every record change; redundant with `.base`; unwieldy for 100+ items. | **Rejected** |
| **B. Embedded `.base` View Only** | Interactive in Obsidian; zero maintenance. | Completely invisible in terminal (`cat`, `glow`), GitHub web UI, and mobile fallback; no executive statistics. | **Rejected as standalone** |
| **C. Managed Summary Chips + Stat Callout + Transcluded `.base`** | Beautiful, compact, high-level metrics; immediate CLI/web visibility; interactive power in Obsidian; minimal git noise. | Requires a synchronization pass (`bob albums sync`) to update counts. | **Recommended (Gold Standard)** |

### 5.2 The Recommended Album Summary Layout

The album note body will feature:
1. An executive **Status Filter Chips** bar (matching Bob's task status chips).
2. A compact **Summary Callout** (`> [!summary]`) highlighting key distributions and recent activity.
3. The transcluded Obsidian Base (`![[<album>.base]]`).

#### Concrete Mockup: `~/bob/eat.md`

```markdown
---
parent: "[[body]]"
type: "[[album]]"
record:
  type: restaurant
  label: Restaurant
  emoji: 🍽️
  dated_notes: true
  fields:
    status:
      required: true
      values: {to_try: 🔖 To try, liked: 💚 Liked, not_liked: 🚫 Not liked}
    category: {required: true, suggest: true}
    location: {required: true, suggest: true}
    companions: {values: link, list: true, default: ["[[kelly]]"]}
    visited: {values: date}
    url: {values: url}
---

# Restaurants

Restaurant records live under `eat/`. Browse and filter them interactively in [[eat.base]].

Related: [[body]] [[drink]] [[legacy_eat]]

## Notebooks

> [!notebooks]
>
> - **[[legacy_eat|Legacy restaurant notes]]** — Zorg-era restaurant notes and tables, moved here from eat.md on 2026-11-10.

## Records

[`🍽️ 105 total`](#Records) · [`💚 42 liked`](#Records) · [`🔖 38 to try`](#Records) · [`🚫 25 not liked`](#Records)

> [!summary] Summary
> - **Total:** 105 restaurants across 18 categories
> - **Top Categories:** Italian (22), American (19), Japanese (14), Mexican (11), Coffee (9)
> - **Top Locations:** Garwood (14), Westfield (12), Cranford (11), Summit (8), NYC (15)
> - **Recent Visits:** [[eat/burger_bistro|Burger Bistro]] (2026-11-09), [[eat/track_5|Track 5 Coffee]] (2026-11-04)

![[eat.base]]
```

#### Concrete Mockup: `~/bob/podcasts.md`

```markdown
---
parent: "[[dev]]"
type: "[[album]]"
record:
  type: podcast
  label: Podcast
  emoji: 🎙️
  fields:
    status:
      required: true
      values: {subscribed: 🎧 Subscribed, to_try: 🔖 To try, unsubscribed: 🚫 Unsubscribed}
    category: {required: true, suggest: true}
    url: {values: url}
---

# Podcasts

Podcast show records live under `podcasts/`. Browse and filter them in [[podcasts.base]].

Related: [[dev]] [[lit/podcasts]] [[podcast_ref]]

## Records

[`🎙️ 15 total`](#Records) · [`🎧 9 subscribed`](#Records) · [`🔖 0 to try`](#Records) · [`🚫 6 unsubscribed`](#Records)

> [!summary] Summary
> - **Active Subscriptions (9):** [[podcasts/techmeme|Techmeme Ride Home]], [[podcasts/python_bytes|Python Bytes]], [[podcasts/talk_python|Talk Python to Me]], [[podcasts/practical_ai|Practical AI]], [[podcasts/programming_throwdown|Programming Throwdown]], [[podcasts/the_pete_and_sebastian_show|The Pete and Sebastian Show]], [[podcasts/ted_radio_hour|TED Radio Hour]], [[podcasts/twit|This Week in Tech]], [[podcasts/ai_daily_brief|The AI Daily Brief]]
> - **Primary Categories:** Python (2), Tech News (2), AI (2), General Tech (2), Comedy (1)

![[podcasts.base]]
```

---

## 6. Detailed Design: The Managed `## Albums` Section in Parent Area Notes

### 6.1 Placement and Visual Design

In an Area Note (e.g., `body.md`, `dev.md`, `fun.md`), child albums should be summarized in a dedicated, machine-managed H2 section: `## Albums`.

Following Bob's structural conventions:
- Positioned immediately after `## Notebooks` and before `## Tasks`.
- Encapsulated in a standard callout: `> [!albums]`.
- Content is machine-managed by `bob albums sync` (or unified `bob sync`).
- Each entry displays:
  1. Wikilink to the Album Note: `**[[<album_stem>|<Display Label>]]**`
  2. Emoji badge and total record count: `(<emoji> <count>)`
  3. Formatted status breakdown: `— <count> <status_label> · <count> <status_label> ...`

### 6.2 Visual Mockups

#### In `~/bob/body.md`:
```markdown
## Notebooks

> [!notebooks]
>
> - **[[legacy_body|Legacy body notes]]** — Zorg-era body notes, moved here from body.md on 2026-11-10.

## Albums

> [!albums]
>
> - **[[eat|Restaurants]]** (🍽️ 105) — 42 liked · 38 to try · 25 not liked

## Tasks
[`⚪ 0 open`](#Tasks) · [`🔵 1 next/wip`](#Tasks#Next%20&%20In%20Progress) · [`🔴 6 blocked`](#Tasks#Blocked) · [`🟢 3 done/canceled`](#Tasks#Done%20&%20Canceled)
```

#### In `~/bob/dev.md`:
```markdown
## Notebooks

> [!notebooks]
>
> - **[[ai|AI]]** — Definitions and notes on LLMs, AI assistants, and agentic coding tools.
> ...

## Albums

> [!albums]
>
> - **[[podcasts|Podcasts]]** (🎙️ 15) — 9 subscribed · 6 unsubscribed

## Tasks
[`⚪ 0 open`](#Tasks) · `🔵 0 next/wip` · [`🔴 16 blocked`](#Tasks#Blocked) · [`🟢 1 done/canceled`](#Tasks#Done%20&%20Canceled)
```

#### In `~/bob/fun.md`:
```markdown
## Albums

> [!albums]
>
> - **[[tv|TV Shows]]** (📺 24) — 3 watching · 12 watched · 5 to watch · 4 dropped
> - **[[movies|Movies]]** (🎬 48) — 35 watched · 13 to watch

## Tasks
...
```

---

## 7. Canonical SASE Glossary Terms

These two terms should be added to `sase/memory/glossary/`.

### 7.1 Proposed `sase/memory/glossary/album-note.md`

```markdown
---
type: reference
---

# Album Note

*Requested · project*

aka album, collection note

A Bob vault Markdown file located at the vault root with frontmatter `type: "[[album]]"`
that defines, manages, and catalogs a structured collection of [[record-note]]s.
An album note strictly owns the immediate folder of the same name (`<stem>/`),
where all its individual member records reside.

Its frontmatter MUST declare exactly one `parent:` pointing to an [[area-note]]
(or top-level [[project-note]]), establishing the root-parent lineage for all
records within its collection. It MUST also declare a `record:` mapping specifying
the schema (record type id, display label, emoji, dated notes setting, field definitions,
and legacy keys) that governs every member record.

The body of an album note carries an executive status summary and transcludes its
companion Obsidian Base (`![[<stem>.base]]`). It never holds `#task` checkboxes,
task links, or Pomodoro ledger entries; action items relating to the collection
belong in its parent area.

Every parent area note catalogs its child albums under a machine-managed `## Albums`
section maintained by `bob albums sync`. Distinct from an [[area-note]], a [[project-note]],
a [[notebook]], and a [[reference-note]]. See `docs/records.md`.
```

### 7.2 Proposed `sase/memory/glossary/record-note.md`

```markdown
---
type: reference
---

# Record Note

*Requested · project*

aka record

A Bob vault Markdown file representing one discrete, durable entity (such as a
restaurant, podcast show, TV series, or movie) filed inside an [[album-note]]'s
owned directory (`<album>/<stem>.md`).

Its frontmatter declares `parent: "[[<album>]]"` pointing to its owning album note,
and `type: "[[<record_type>]]"` identifying its schema. Its additional frontmatter
properties conform strictly to the `record.fields` schema defined in its album note.
Optional bullets and dated logs appear under `## Notes`.

A record note never holds `#task` checkboxes or Pomodoro timespans. Its root parent
is derived by walking up through its album note to the enclosing [[area-note]].
Capture creates record notes via `<title> @<album>/` syntax, and the `bob records`
CLI manages validation, linting, and field updates. Distinct from an [[album-note]],
a [[notebook]], and a [[reference-note]]. See `docs/records.md`.
```

---

## 8. Adjustments to Requirements & Design Refinements

Based on this research, the following refinements to the original plan are recommended:

1. **Strict Stem-to-Folder Identity (`<album>.md` <-> `<album>/`)**:
   Do not allow arbitrary directory configurations in frontmatter. Enforce that the album note stem matches the folder name exactly (`eat.md` owns `eat/`, `podcasts.md` owns `podcasts/`, `tv.md` owns `tv/`, `movies.md` owns `movies/`). This guarantees unambiguous `@route/` capture resolution.
2. **Consolidation of `podcast.md` and `podcasts.md`**:
   The existing `podcast.md` (which was scaffolded as an inert Type Note) should be merged into `podcasts.md`. `podcasts.md` will become the official Album Note (`type: "[[album]]"`). A redirect or alias for `[[podcast]]` can be maintained if needed for Obsidian graph links.
3. **Hybrid Album Summary Instead of Plain Record Lists**:
   Avoid generating static markdown tables of 100+ items in album notes. Instead, adopt the hybrid pattern: filter chips (`[`🍽️ 105 total`]`), compact summary callout (`> [!summary]`), and the transcluded Obsidian Base (`![[eat.base]]`).
4. **Mirror the Notebook Engine Architecture (`bob albums`)**:
   Implement the album management commands using the exact same robust pattern used in `src/native/notebooks/`:
   - `bob albums list`: Inspect all albums, their parent areas, schemas, and counts.
   - `bob albums check`: Lint album frontmatters, check directory consistency, and ensure unbroken parent walks.
   - `bob albums sync`: Pure byte-range updater that updates `## Records` summaries in album notes and `## Albums` sections in parent area notes.

---

## 9. Recommended Implementation Plan

### Phase 1: Engine & Schema Parser (`bob-cli`)
- Update `src/native/records/schema.rs` to parse `record:` mappings from album note frontmatters (`type: "[[album]]"`).
- Implement schema discovery in `RecordCatalog`: scan vault root notes for `type: "[[album]]"` to resolve schemas dynamically, falling back to `config.yml` during migration.
- Add `src/native/albums/` module (modeled after `src/native/notebooks/`) containing `scan.rs`, `catalog.rs`, and `region.rs` to manage the `## Albums` callout in Area notes.

### Phase 2: Vault Migration & Dezorging
1. **Dezorg `eat.md`**:
   - Extract legacy Zorg tables into `legacy_eat.md` (`type: "[[notebook]]"`, `parent: "[[eat]]"`).
   - Update `eat.md`: set `parent: "[[body]]"`, `type: "[[album]]"`, embed `record:` schema, add `## Notebooks` callout linking to `[[legacy_eat]]`.
2. **Consolidate `podcasts.md`**:
   - Update `podcasts.md`: set `parent: "[[dev]]"`, `type: "[[album]]"`, embed `record:` schema.
   - Retire/redirect `podcast.md`.
3. **Standardize `tv.md` and `movies.md`**:
   - Set `parent: "[[fun]]"`, `type: "[[album]]"`, embed schemas.

### Phase 3: Area Note Catalogs & Memory Updates
- Run `bob albums sync` to stamp `## Albums` into `body.md`, `dev.md`, and `fun.md`.
- Add `album-note.md` and `record-note.md` to `sase/memory/glossary/`.
- Update `docs/records.md` and `AGENTS.md` to reflect the new album architecture.
- Remove deprecated `records:` block from `~/.config/bob/config.yml`.
