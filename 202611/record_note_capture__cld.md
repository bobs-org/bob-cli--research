# Record Notes: Capturing Custom-Typed Notes (`@eat/`)

*Research report · researcher `cld` · 2026-11-08 · bob-cli 0.4.0, capture grammar 19*

## TL;DR

- **Yes, build it, but keep it small and make it reuse what exists.** Capture should
  gain exactly one new spelling, `@<dir>/`. Everything else should come from existing
  pieces: authored bullets, `capture-complete` pickers, the dry-run preview, the atomic
  batch writer, and `%t` templates.
- **Rename the concept to Record Notes.** In Bob, "type" already means the Task Type
  (`#fix`, the `types:` config, `bob types`). The vault's `type: "[[restaurant]]"`
  frontmatter stays exactly as it is. Only the config key, the CLI noun, and the glossary
  term change.
- **Put the schema in `config.yml` under `records:`.** That file is chezmoi-managed and
  shared across hosts, and it already uses the `values: date | [list]` vocabulary of
  `properties:`.
- **Capture reads like the note it writes.**
  ```text
  Tito's Burritos @eat/
  - status:: liked
  - category:: Burritos
  - location:: Cranford
  - Ghost pepper burrito is too hot
  ```
  This creates `eat/titos_burritos.md`. The `key:: value` bullets become frontmatter and
  the other bullets become `## Notes`.
- **Easy input comes from bob, and the Mac app only shows it.**
  - bob reports which required fields are missing and offers the values for each one:
    enum labels, values already used in the vault (ranked), `today`, and wikilinks.
  - On the Mac, Tab steps through the missing fields. Each accepted value appears in the
    draft as visible text, so the draft itself is the form.
  - A **Record Card** and a **New-note preview** make this pleasant to use. On the CLI, a
    missing field is refused with an example draft to copy.
- **Reliability needs a validator, not just a writer.** `bob records check` lints every
  record folder. The two restaurant notes created since the zorg migration were both
  written by agents, and both already differ from the established shape.
- **Kinds:** `restaurant` and `podcast` now (both already exist as types). `show` (`tv/`)
  and `movie` (`movies/`) next, because there is clear demand. Books, people, logs, and
  quotes should **not** become record kinds.

## 1. What exists today

### 1.1 The vault's two de-facto record collections

| Folder | Notes | `type:` | Index note | Dashboard |
| --- | --- | --- | --- | --- |
| `eat/` | 92 | `"[[restaurant]]"` (all 92) | `eat.md` (legacy zorg table) | `eat.base`, 6 views (cuisine, favorites, by town, recent, not-for-us, gallery) |
| `podcasts/` | 15 | `"[[podcast]]"` | `podcasts.md` (embeds the base) | `podcasts.base` |

The type notes `restaurant.md` and `podcast.md` are children of `type.md`. They hold prose
that describes the type and nothing else. Across the vault, frontmatter `type:` values
are: `day` 1270, `ref` 1238, `project` 103, `restaurant` 92, `done` 31, `area` 20,
`podcast` 15, `mail` 6, `article` 3.

Frontmatter keys found across the 92 `eat/` notes:

| Key | Present | Observed values |
| --- | --- | --- |
| `parent` | 92 | always `"[[eat]]"` |
| `type` | 92 | always `"[[restaurant]]"` |
| `title` | 92 | display name, e.g. `"Tito's Burritos"` |
| `status` | 92 | `liked` 85, `not_liked` 7 |
| `category` | 92 | 37 distinct strings, including typos (`Cheeseteaks`, `Cheesteaks / Wings`); `null` ×6 |
| `location` | 92 | a mix of plain towns (`"Westfield"`) and block-anchor links (`"[[nj_towns#^z-241117-0b\|cranford]]"`) |
| `companions` | 92 | `[[kelly]]` ×90, `[]` ×2 |
| `lid`, `source_*` | 90–91 | zorg migration provenance |
| `visited`, `created` | 2 / 1 | only on the post-migration notes |

`eat.base` cleans up the category mess at read time: its 22-branch `cuisine` formula
groups categories by substring. That formula shows the cost of having no schema.

### 1.2 How record notes get created today

Only **two** restaurant notes have been created since the zorg migration (June 2026), and
both came from agents. Commit `a9480c786` reads "feat: add Rush Bowl restaurant note".
Both already differ from the established shape:

- `companions: []`, although 90 of 92 notes say `[[kelly]]`;
- `lid: null`;
- quoted `visited` dates;
- a different `created` timestamp style.

So the real problems are friction and drift, not volume. Creation is rare, yet nothing
holds the shape stable.

### 1.3 Relevant bob-cli precedents

- **Creating a note from capture is already a feature.** `@route^id@` creates a project
  note at `<route>_<id>.md` with `parent`, `type`, `status`, and `created` frontmatter.
  It reroutes authored bullets into sections, uses the staged, all-or-nothing batch
  writer (including the "note was created on disk after planning" guard), and has
  teaching refusals (`docs/capture.md` §Project notes; `src/native/capture_project_note.rs`).
- **bob already creates typed notes in a folder.** `bob gmail new` writes `mail/` notes
  with `type: "[[mail]]"`, using a slug and a counter suffix
  (`src/native/gmail/note/path.rs`). The bob-mail Obsidian plugin just calls it and
  opens the result.
- **Decision `capture-sigils-say-where-what-how`:** `@` says where, `#` names a place or
  a type, and `%` says how. It reopens "when Bryan … adds a sigil". A design that adds no
  sigil does not reopen it.
- **Decision `capture-bullets-mirror-the-task-block`:** the draft should read like the
  block it writes.
- **Decision `mac-capture-is-a-thin-client`:** grammar, completion, preview, and writes
  all live in bob. The Mac app only renders and orchestrates. Every capture feature lands
  twice (bob first, then Swift behind macOS CI), and the JSON grows additively.
- **The config already has a value vocabulary.** `properties:` in `~/.config/bob/config.yml`
  types bullet properties as `values: date | local_task_id | priority | [list]`. The
  Obsidian Task Card picker is driven by it. The file is chezmoi-managed
  (`dot_config/bob/config.yml`), so every host sees the same config.
- **`@eat/` is free today.** `bob capture-parse "Tito's Burritos @eat/"` reports
  mode `task` with the literal body `Tito's Burritos @eat/`: no route and no diagnostic.
  `@eat/^titos` is already a hard error (`invalid_task_block_id_route`). Claiming both is
  a grammar bump, but neither form has a useful meaning now.
- **There is one Mac interaction to handle.** In the panel, typing `/` after a route is a
  Bob-decided alias for `#` (it opens the section menu). A `/` stays literal "where Bob
  already reads it as part of a field". After a configured record folder, Bob must answer
  "literal", or "open the record flow". `\` still aliases `#`.
- **The Mac surfaces available to build on** (from a read-only survey of bob-mac-capture):
  - the inline completion list, which is generic: any new completion `context` renders
    as neutral rows with no Swift changes;
  - the large picker card;
  - single-field prompt cards;
  - choice cards;
  - a dry-run **Preview pane** with diff cards;
  - the Similar-tasks band;
  - the template shelf.

  There is **no** multi-field form and **no** whole-new-note preview today. Tab accepts
  completions, and accepted rows can carry a `continuation` that opens the next picker.
  That is how chained pickers already work.
- **CLI conventions** (`cli_rules`):
  - nest commands under a noun that has a membership rule;
  - a bare group may only default to a read-only member;
  - every long option gets a short alias;
  - never add subcommands under `bob capture`.
- **Phones are a known gap.** Keep imports are "never capture grammar"
  (`docs/gkeep.md`), so phone captures cannot use this syntax.

### 1.4 Prior art outside Bob

Every typed-object tool converges on the same small model: a type with a field template
and a handful of field kinds.

- **Tana:** a supertag carries fields with a *Required* setting, and option fields can
  draw from another supertag's nodes.
- **Capacities:** object types carry properties, and an "object select" property links
  one type to another.
- **Metadata Menu** (Obsidian; its successor *Fileclass* is built on Bases): a fileClass
  defines Input, Select, Multi, Date, File, Number, and Boolean fields. Notes map to a
  class by frontmatter, tag, or **folder path**.
- **Obsidian Bases:** the *New* button already writes a view's filter values into a new
  note's properties. Community plugins (*Bases Note Templates*, *Bases Templates*) add
  templates, and forum threads report gaps such as wikilink filters and sidebar bases.

What to take from this:

1. Keep the set of field kinds small (`text`, `enum`, `date`, `link`, `url`, `number`,
   plus a `list` modifier).
2. Map a folder to a type 1:1. Bryan already does this.
3. Obsidian-side tools don't reach the Mac capture panel or the CLI, and they don't check
   required fields. They complement this design rather than replace it.

## 2. Critique: is this a good idea?

**Yes, with conditions.** It is worth doing because it fixes three real problems:

1. Creating a record today means hand-writing YAML or asking an agent.
2. Nothing checks the shape, and drift has already started (§1.2).
3. Bryan's actual watch, eat, and listen history is scattered across tasks that disappear
   into `done/` (§4).

It is risky because capture is already the densest part of Bob: a 10,180-line guide,
grammar revision 19, and nearly every ASCII sigil already assigned. The feature also
lands twice (bob, then Swift). Creation volume is low, about one restaurant a month, so
the feature only pays off if it is:

- **declarative**, with no per-kind code;
- **one new spelling**, not a new sub-language;
- **validated**, because a schema that only the writer uses will drift like the agents'
  notes did;
- **useful outside capture** (agents, Command Mode, lint) even before the Mac half ships.

**What I would not build:** views and dashboards (Bases already does this well), relations
and computed fields, auto-enrichment from the web, per-kind code paths, or
Templater-template evaluation inside bob.

### 2.1 Alternatives considered

| Approach | Verdict |
| --- | --- |
| **Obsidian-only:** Bases *New* button, Templater folder templates, Metadata Menu / Fileclass | Good inside Obsidian, but unreachable from the Mac panel and CLI, with no required-field enforcement and no agent API. Keep it as a complementary path; `bob records check` catches what it misses. |
| **Agent-only:** "add Rush Bowl to eat" | This is what happens today. It is slow, costs tokens, and drifts (§1.2). A `bob records new` command gives agents a contract instead. |
| **Positional table rows**, like the old zorg table: `Tito's \| liked \| Burritos \| Cranford` | Fastest to type and familiar, but not self-describing. It breaks when optional fields are added or the schema changes, and errors can't point at a field. Rejected. |
| **`#restaurant` (type sigil)** | `#` already names the Task Type. It would collide with the `types:` vocabulary and the `type_not_configured` refusals. Rejected. |
| **`%eat` / `%r` (directive)** | `%` holds single-letter "how" directives (`%c` `%n` `%t` `%l`), and a kind is a "where". Rejected. |
| **A new sigil** | Reopens the sigils decision, and few free characters remain. Rejected. |
| **`@eat` → create a record** | Breaking: `@eat` already routes a task into `eat.md`. Rejected. |
| **`@eat/` (path spelling)** | `@` still says where, and the text is literally the folder the note lands in. It is free today, needs no new sigil, and can later extend to `@eat/<stem>` for existing records. **Chosen.** |
| **Schema in the vault** (YAML inside `restaurant.md`) | Appealing because the data travels with the vault. But nested YAML renders badly in Obsidian Properties, a schema typo would break capture from a synced note edit, and every other Bob vocabulary (`types:`, `properties:`, `plan:`) lives in config. Rejected; `restaurant.md` stays the human doc. |

## 3. Requirement adjustments (clearly called out)

1. **Name: "custom types" → *Record Notes*, defined by *record kinds*.**
   - "Type" already means three things in Bob: Task Type, `[type::]`, and frontmatter
     `type:`.
   - Config key: `records:`. CLI: `bob records`. Glossary: *Record Note*, *Record Kind*.
   - The frontmatter stays `type: "[[restaurant]]"`, so `eat.base` and the plugins are
     unaffected.
2. **The schema lives in `config.yml` (`records:`), not in the vault.**
3. **"Must be defined" becomes "required, unless the kind declares a default."**
   - `companions` defaults to `[[kelly]]`, which 90 of 92 notes already have.
   - `visited` defaults to `today`.
   - bob-owned fields (`parent`, `type`, `title`, `created`) are never typed; bob writes
     them.
4. **Optional fields: yes.**
   - Only declared fields may be written. Capture refuses unknown keys with a
     did-you-mean.
   - `check` reports unknown keys on existing notes as `extra`, and an allowlist
     (`source_*`, `lid`, `zorg_id`) silences migration provenance.
5. **The folder is the capture spelling, and kind and folder are 1:1.**
   - You write `@eat/`, not `@restaurant/`. `@restaurant/` gets a teaching refusal.
   - In v1 a folder must be a single path segment, so it fits the route alphabet.
6. **Add a validator (`bob records check`).** It is part of "reliable"; it is not
   optional.
7. **Add an agent/CLI API (`bob records new`)** that shares the capture planner.
8. **Plan for "add to an existing record" (phase 2).** For restaurants, revisits outnumber
   first visits. `@eat/<stem>` is reserved now so creation and appending share one
   spelling family.
9. **Duplicates are errors, not suffixes.**
   - Gmail threads get `_2` suffixes; a second `titos_burritos.md` is always a mistake.
   - An exact path collision refuses.
   - A near-title match shows a heads-up.
10. **Out of scope for v1:** capture from the phone through Keep, web enrichment (titles
    from URLs, maps lookups), and tasks inside record notes.

## 4. Which kinds should exist?

I checked every collection-like note in the vault.

| Candidate | Evidence | Verdict |
| --- | --- | --- |
| **restaurant** (`eat/`) | 92 notes, a 6-view base, a type note | **v1.** Also consider adding `to_try` to `status` so the 12-item `maybe_eat.md` wishlist could later become a "🔖 To Try" view (optional, later). |
| **podcast** (`podcasts/`) | 15 notes, a base, a type note; stems are hand-picked (`talk_python`, `techmeme`) | **v1**, config only. This kind is why the explicit-stem override (`@podcasts/^talk-python`) exists. |
| **show** (`tv/`) | `prj_plex.md` "Active TV Shows"; 23 `TV SHOW:` tasks; 175 `#plex` mentions in 66 files; `tv.md` already sits at the root as an index | **v1.1.** Today this is tracked as tasks that vanish into `done/` when finished, so the vault has no watch history or verdicts. Fields: `status` (to_watch / watching / watched / dropped), `service`, `recommended_by` (people links; "INSPIRED BY: %eric/%nona" appears often), `verdict`. |
| **movie** (`movies/`) | 5 "Watch … movie with Kelly" tasks in `love.md`; "Download '…' movie" tasks | **v1.1**, same field shape as `show`. Two kinds rather than one `watch/`, because the lifecycles differ (movies rarely sit in "watching") and Bryan names them separately. |
| book | `books.md` is legacy; refs (1,238 `type: [[ref]]`) own books, PDFs, and reading tasks | **No.** References are already the typed-note system for things you read. |
| podcast episode | `podcast_ref.md`, `lit/podcasts` | **No.** These are refs too. |
| person | `people.md` `%ldap` table; `kelly.md` is an *area* | **No (not now).** Mentions and areas have wide reach in the vault, and a person is not a flat record. |
| liquor store (`drink.md`) | 2 rows | Fold into `restaurant` with category "Liquor Store", or skip. |
| trails, surf, vet, haircut, dentist | logs or single notes | **No.** These are logs, not collections of things. |
| quotes | `quote.md` is one note whose block IDs exist for embedding | **No.** The single note is deliberate. |

Once the engine exists, adding a kind costs one config block (plus `bob records init`).
That makes the TV and movie decision cheap to revisit.

## 5. Design

### 5.1 Schema (`records:` in `config.yml`)

```yaml
# Record notes: one note per thing, in its own folder (docs/records.md in bob-cli).
# Capture creates one with `<title> @<dir>/`; `bob records check` lints the folder.
records:
  restaurant:
    dir: eat                      # folder (one segment); also the capture spelling @eat/
    emoji: 🍽️                     # chip/card/human-output glyph (optional)
    fields:                       # frontmatter order = this order
      status:
        required: true
        values:                   # closed enum; labels are display-only
          liked: 💚 Liked
          not_liked: 🚫 Not Liked
          to_try: 🔖 To Try
      category:
        required: true
        suggest: true             # open vocabulary: offer existing values from eat/
      location:
        required: true
        suggest: true
      companions:
        values: link
        list: true
        default: ["[[kelly]]"]
      visited:
        values: date
        default: today
    allow_extra: [lid, source_*]  # legacy keys `check` tolerates
  podcast:
    dir: podcasts
    emoji: 🎙️
    fields:
      status: {values: {subscribed: 🎧 Subscribed, unsubscribed: 🚫 Unsubscribed}, default: subscribed}
      category: {required: true, suggest: true}
      url: {values: url, required: true}
    allow_extra: [zorg_id, source_*]
```

**Field kinds.** The `values:` key reuses the `properties:` vocabulary.

| `values:` | Accepts | Completion offers | Written as |
| --- | --- | --- | --- |
| *(omitted)* | free text | existing values, if `suggest: true` (by frequency, with counts) | `"…"` (YAML-escaped) |
| list or `{value: label}` map | one listed value | the values, shown with their labels | bare token (`liked`) |
| `date` | `YYYY-MM-DD`, `today`, `yesterday` | today, yesterday (with dates) | bare ISO `2026-11-08` |
| `link` | a `[[wikilink]]` (or a bare name, which bob wraps) | previously used values, then the existing `[[` note completion | `"[[kelly]]"` |
| `url` | `http(s)://…` | none | bare |
| `number` | integer or decimal, optional `min`/`max` (e.g. a 1–5 rating) | none | bare |

`list: true` makes a field multi-valued. You can repeat the bullet or comma-separate
values outside `[[…]]`. bob writes YAML block lists.

**Config validation** happens at load and is a config error, the same way other blocks
fail:

- Kind names match `[a-z][a-z0-9_]*`.
- Built-in types are reserved: `project`, `area`, `ref`, `day`, `done`, `mail`,
  `article`.
- `dir` is a single relative segment, unique across kinds.
- Field keys match `[a-z][a-z0-9_]*`. `parent`, `type`, `title`, and `created` are
  reserved.
- Enums must be non-empty.
- A `default` must itself validate.
- `suggest` only applies to text and link fields.

### 5.2 The file bob writes

**Path:** `<dir>/<stem>.md`.

- The default stem comes from the title: NFKD-fold, `&` → `and`, drop apostrophes
  (`'` `’`), turn every other non-alphanumeric run into `_`, trim, lowercase.
- **This rule reproduces 91 of the 92 existing `eat/` filenames.** The exception is
  `&grain` → `and_grain` vs `andgrain`.
- An explicit stem, `@podcasts/^talk-python`, follows the project-note ID rule
  (`A-Z a-z 0-9 -`, with `-` → `_`).
- An existing or already-staged path refuses with `record_exists`.

**Frontmatter** order and quoting match the existing notes:

```markdown
---
parent: "[[eat]]"
type: "[[restaurant]]"
title: "Tito's Burritos"
status: liked
category: "Burritos"
location: "Cranford"
companions:
  - "[[kelly]]"
visited: 2026-11-08
created: 2026-11-08T12:41:07-05:00
---

# Tito's Burritos

## Notes

- 2026-11-08: Ghost pepper burrito is too hot
```

- `parent` defaults to `"[[<dir>]]"` when `<dir>.md` exists (`eat.md`, `podcasts.md`,
  `tv.md` all do). It can be overridden with a per-kind `parent:`.
- `created` reuses the project-note timestamp helper and honours `BOB_NOW`.
- Empty optional fields are omitted, never written as `null`.

**Body:**

- `# Title`, then `## Notes`. The empty heading is kept, exactly like `chopt.md`.
- First-level note bullets are dated (`- YYYY-MM-DD: …`), matching the two
  post-migration notes. This turns `## Notes` into a visit log that phase 2 appends to.
  `dated_notes: false` turns it off.
- An ALL-CAPS first-level bullet with nested bullets becomes a `## Title Case` section,
  using the same rule and writer as project notes. So `- MENU` with nested bullets
  becomes `## Menu`.

### 5.3 Capture grammar (revision 20)

| Form | Meaning |
| --- | --- |
| `<title> @<dir>/` or `@<dir>/ <title>` | Create a record of the kind whose `dir` is `<dir>`; the stem comes from the title |
| `<title> @<dir>/^<stem>` | Same, with an explicit stem |
| first-level `- <key>:: <value>` | Set a declared field; the key match is exact |
| first-level `- <key>::` (empty) | Incomplete: needs `record_value` |
| any other first-level bullet (+ nested) | A dated `## Notes` entry, or a `## Section` for ALL-CAPS with nested bullets |
| `@<dir>/<stem>` (no `^`) | **Reserved** for phase 2 (existing record). In v1 it refuses with a teaching message. |

**Rules:**

- The parent line's text, after markers are removed, is the title. An empty title gives
  `needs: ["record_title"]`.
- A record item's own route beats `@@`, like every other local route.
- Multi-item drafts work, and the batch stays atomic. `%t` templates compose for free,
  which makes bulk imports one paste:
  ```text
  {0} @podcasts/^{1} %t
  - category:: {2}
  - url:: {3}

  "Talk Python to Me" talk-python python https://talkpython.fm
  ```
- A record item is claimed whole, so a URL inside `- url:: …` is a field, not a
  reading-queue job.
- **Refused on record items, each with a message naming the marker**
  (`record_marker_unsupported`):
  - `#type`, `s:<N>`, `$<N>`
  - `%c`, `%n`, `%l`
  - `&`, `*`, `~`, `!`, `+`
  - session operators
  - a ` :id` / ` ^id` task bullet

  These remain open for later. For example, a future `- Watch it with Kelly ^watch` could
  put a task inside a movie record.
- **Teaching refusals** in Bob's established voice:
  - `` `eat/` is not a record folder; record folders: eat/, podcasts/ (add one under `records:` in config.yml) ``
  - `` `@restaurant/` names the kind; restaurant notes live in eat/ — write `@eat/` ``
  - `` `cat` is not a restaurant field; did you mean `category`? (fields: status, category, location, companions, visited) ``
  - `` `status:: loved` — restaurant status is liked, not_liked, or to_try ``
  - `` record already exists: eat/titos_burritos.md (open it, or add a note to it with `@eat/titos_burritos` once that lands) ``

**`capture-parse`** additions are additive JSON. The new mode is `record_note`, and a
`record` object carries:

- `kind`, `dir`, `stem`, `stem_source` (`title`|`explicit`), `path`, `title`, `emoji`;
- `fields[]`, each with `key`, `label`, `required`, `list`,
  `state: set|missing|default|invalid`, the values, and the byte `range`.

New spans:

- `record_route`, `record_stem`
- `record_field_key`, `record_field_value`

New needs:

- `record_title`
- `record_field` (a required field with no default is missing)
- `record_value` (an empty `key::`)

Parse reads config only, never the vault, which keeps the existing parse contract.

### 5.4 Making input easy (the core UX)

The principle is **a form that is just the draft.** Every assist is an ordinary,
undoable text edit chosen by bob, so stash, undo, templates, the CLI, and
`capture-rewrite` all keep working unchanged.

1. **Discover.** `@` route completion gains record rows, for example
   `eat/  🍽️ new restaurant · 92 notes`. `bob capture-targets` lists record folders
   with `kind: record`.
2. **Tab-through.** When the caret is in a record item that is missing required fields,
   `capture-complete` returns context `record_value` for the next missing field.
   - Rows are enum labels (💚 Liked …), vault values ranked by frequency
     (`Breakfast · 18`, `Coffee · 11`, …), date shortcuts, or links.
   - Accepting a row inserts `\n- <key>:: <value>` at the end of the item's field block.
     It carries a `continuation`, so the next missing field's list opens straight away.
   - Typing filters the list. For an open vocabulary, typing a new value is fine; a value
     close to an existing one (`Cheeseteaks` vs `Cheesesteaks`) gets a soft
     `record_value_near` warning.
   - Escape stops at any point, and what is already typed stays.
3. **Field names.** On a fresh `- ` bullet inside a record item, the `record_field`
   context offers the fields not yet set, required ones first.
4. **Values in place.** After `key:: `, the same `record_value` list appears.
   `[[` falls through to the existing wikilink completion.
5. **Generic clients already work.** An unknown completion context renders as neutral rows
   with no Swift change, so an older app degrades gracefully.

**The beautiful version (Mac phase): the Record Card.** It is drawn from the parse
`record` object and sits where the picker card sits today:

```text
╭─ 🍽️  New restaurant ─────────────────────── eat/titos_burritos.md ─╮
│  ● Status       💚 Liked                                           │
│  ○ Category     Breakfast · Coffee · Pizza · Sushi · …   ⇥ fill    │
│  ○ Location     Cranford · Westfield · Clark · NYC · …              │
│  ✓ Companions   [[kelly]]                              default     │
│  ✓ Visited      today · 2026-11-08                     default     │
│  · 1 note                                                           │
╰──────────────────────── ⇥ next field · ⏎ create · ⌃⏎ create + open ─╯
```

- **The status line** reads, for example, "Restaurant needs category and location —
  press Tab".
- **The New-note preview card** renders bob's dry-run `note_files[]` entries
  (`path`, `kind`, `fields[{key, value, display}]`, `body`). It shows a property sheet
  with labels (💚 Liked) rather than raw YAML, then the body. The existing Preview pane
  only shows block diffs, so this is the one new view.
- **Similar records heads-up.** This reuses the Similar-tasks band pattern
  (`similar-tasks-are-a-settled-heads-up`). After typing settles, a near-title match in
  the same folder shows "Already in eat/: Tito's Burritos — 💚 liked · Burritos". In
  phase 2 its action rewrites the draft to `@eat/titos_burritos`.

**CLI ergonomics.** `bob capture` refuses an incomplete record with a ready-to-copy draft:

```text
bob capture: a restaurant note needs 2 more fields
  Tito's Burritos @eat/
  - status:: liked
  - category:: …            Breakfast · Coffee · Pizza · Sushi
  - location:: …            Cranford · Westfield · Clark · NYC
```

For scripts and agents, the same planner is exposed as a flag-driven command:

```sh
bob records new restaurant "Tito's Burritos" -s status=liked -s category=Burritos \
  -s location=Cranford -n "Ghost pepper burrito is too hot"
```

It also shows up automatically in Obsidian Command Mode, because it is declared through
`bob __catalog` slots.

### 5.5 `bob records` command group

Subcommands are alphabetical. A bare `bob records` means `list` (read-only).

| Command | Purpose |
| --- | --- |
| `check [KIND] [-f json]` | Lint each folder: wrong or missing `type`, missing required fields, invalid enum values, unknown keys (`extra`), records of the kind outside its folder, folder notes without the type, and near-duplicate values (`Westfield` vs `[[…\|westfield]]`). Exits 1 on errors. Suitable for `nightly`. |
| `init KIND` *(phase 3)* | Scaffold a kind's folder, its type note (`parent: "[[type]]"`), an index note that embeds the base, and a starter `.base`. |
| `list` | Kinds with emoji, folder, count, and required fields. |
| `new KIND TITLE [-d/--dry-run] [-f/--format] [-n/--note TEXT]… [-o/--open] [-s/--set KEY=VALUE]… [-S/--stem STEM]` | Create one record through the capture planner. |
| `show KIND` | The schema plus each suggest field's value catalog (top values and counts). |

### 5.6 Reliability

- **One engine.** A new `src/native/records/` module holds `schema`, `catalog` (a scan of
  values, stems, and titles), `render`, and `plan`. Capture items and `records new` both
  call `plan`. The commit goes through the existing staged-write path, with its
  created-after-planning guard and rollback.
- **Exact matching at commit time**, as in the sigils decision. Completion only assists;
  it never decides what gets written.
- **Additive JSON, plus a grammar bump to 20.** Under the release-train decision, the
  newly claimed `@dir/` forms count as a breaking change, so they are marked `!`.
- **Determinism.** Fixed field order and quoting, the `BOB_NOW` clock, and golden tests
  against real notes (`titos_burritos`, `brown_fox_coffee_box`, `talk_python`).
- **Check, not just write.** `check` turns the schema into a contract that holds for all
  writers: Obsidian's Bases *New* button, agents, and hand edits.

### 5.7 Beautiful output

Human `bob capture` output for a record:

```text
✓ 1/1  🍽️ new restaurant  eat/titos_burritos.md
        💚 Liked · Burritos · Cranford · with Kelly · 1 note
```

`bob records check` prints one colored line per finding, grouped by kind, and ends with a
summary such as `92 restaurants · 0 errors · 6 warnings (category missing)`.

## 6. Phased plan

| Phase | Scope | Value on its own |
| --- | --- | --- |
| **1. bob-cli engine** | `records:` config and validation; `records list/show/check/new`; stem rule; renderer; glossary terms (*Record Note*, *Record Kind*) and a decision record | Agents and Command Mode get a contract; `check` exposes today's drift |
| **2. Capture grammar 20** | `@dir/` and `@dir/^stem` items; field and note bullets; parse spans, needs, and the `record` object; completion contexts `record_value` and `record_field` with continuation; `/` stays literal after a record folder in `capture-rewrite`; dry-run `note_files[]`; refusals; `capture-targets` rows; docs | Full CLI capture, and generic Mac completion with no Swift |
| **3. Mac** | Record Card, New-note preview card, record rows in `@` completion, status-line copy (macOS CI gated) | The beautiful flow |
| **4. Existing records and more kinds** | `@eat/<stem>` appends dated Notes, and `- key:: value` updates frontmatter (shown as an exact diff in the preview); completion after `@eat/` lists existing records plus a "＋ New restaurant" row; Similar-records action; `show` and `movie` kinds; optional `maybe_eat` → `to_try` migration; `records init` | Revisits, and watch history |

## 7. Open questions for Bryan

1. Add `to_try` to restaurant `status`, and eventually fold `maybe_eat.md` into
   `eat/`?
2. Should `category` stay an open vocabulary (suggested, with near-duplicate warnings), or
   become a closed cuisine enum that would make the `eat.base` formula unnecessary?
3. `tv/` + `movies/` (my recommendation) or a single `watch/` with a `format` field?
4. Date-stamp `## Notes` bullets by default (my recommendation), or keep them verbatim?
5. `location`: keep free text with suggestions, or normalize to town-note links? This
   only matters for `check`'s near-duplicate report.
6. Should a record ever hold tasks (for example, "Watch it with Kelly" inside a movie
   record)? The v1 refusal leaves room for it.

## 8. Recommended solution

Build **Record Notes**:

- a declarative `records:` block in the shared `config.yml`;
- a `bob records` group (`list`, `show`, `check`, `new`) on top of one records engine;
- one new capture spelling, `<title> @<dir>/` (with an optional `^stem`), whose
  first-level `key:: value` bullets become frontmatter and whose other bullets become
  dated `## Notes`.

Make input easy in three ways:

1. bob-driven completion that steps through the missing required fields, offering enum
   labels, the vault's existing values, `today`, and wikilinks, with every accepted value
   landing in the draft as visible text;
2. ready-to-copy refusals on the CLI;
3. a Record Card and New-note preview on the Mac.

Keep it reliable with:

- all-or-nothing staged writes;
- exact matching at commit time;
- a stem rule proven against the existing filenames;
- duplicate refusals;
- `bob records check`, so the schema also holds for notes written by Obsidian, agents,
  and hand edits.

Ship `restaurant` and `podcast` first, add `show` and `movie` once the engine has proven
itself, and keep books, people, logs, and quotes where they are. Then add phase 4's
`@eat/<stem>`, because adding to records you already have is the more common action.

## Sources

**Vault evidence:**

- the `~/bob/eat/` (92) and `~/bob/podcasts/` (15) notes;
- the `eat.base`, `podcasts.base`, `restaurant.md`, `podcast.md`, `type.md`, `tv.md`,
  `prj_plex.md`, `now_fun.md`, `love.md`, `maybe_eat.md`, `drink.md`, and `people.md`
  notes;
- the vault git log for `eat/`.

**bob-cli:**

- `docs/capture.md`, `docs/articles.md`, `docs/gkeep.md`;
- `src/native/capture_project_note.rs`, `src/native/gmail/note/path.rs`;
- `~/.config/bob/config.yml`;
- live `bob capture-parse` probes.

**Linked repos** (read-only surveys):

- bob-mac-capture: `docs/capture-panel.md`, `docs/keyboard.md`,
  `Sources/BobMacCapture/CapturePanelView.swift`, `CapturePanelModel.swift`,
  `Sources/CaptureCore/*`;
- bob-plugins: `bob-navigation-hotkeys`, `bob-mail`, `bob-command-mode`.

**Decision records:**

- `capture-sigils-say-where-what-how`
- `capture-bullets-mirror-the-task-block`
- `mac-capture-is-a-thin-client`
- `similar-tasks-are-a-settled-heads-up`
- `bob-cli-releases-ride-a-daily-train`

**Web:**

- [Obsidian Bases Note Templates plugin](https://community.obsidian.md/plugins/bases-note-templates)
- [Obsidian Bases Templates plugin](https://community.obsidian.md/plugins/bases-templates)
- [Forum: Bases New button and wikilink filter properties](https://forum.obsidian.md/t/property-not-set-automatically-for-a-new-note-if-bases-filter-criteria-is-wikilink-and-does-not-exist/117347)
- [Forum: Bases: New With Template](https://forum.obsidian.md/t/bases-new-with-template-for-new-button/102639/21)
- [Metadata Menu docs: fields](https://mdelobelle.github.io/metadatamenu/fields)
- [Metadata Menu docs: fileClasses](https://mdelobelle.github.io/metadatamenu/fileclasses)
- [Fileclass plugin (Bases-powered successor)](https://community.obsidian.md/plugins/fileclass)
- [Tana docs: fields](https://www.tana.inc/docs/fields)
- [Tana docs: supertags](https://outliner.tana.inc/docs/supertags)
- [Capacities: is an object type like a database?](https://docs.capacities.io/faq/editing/object-type-like-database)
- [Capacities: custom content types](https://docs.capacities.io/tutorials/custom-content-types)
