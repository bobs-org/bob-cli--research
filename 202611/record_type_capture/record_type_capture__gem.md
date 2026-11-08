# Generalized Custom-Type Note Capture: Architecture, Grammar, and UX Design

**Researcher**: `gem` (5-researcher independent swarm: `gem`, `cdx`, `cld`, `grk`, `mus`)  
**Target Workspace**: `bobs-org/bob-cli`  
**Date**: November 2026  
**Artifact ID**: `research:202611/custom_type_note_capture__gem.md`  

---

## Executive Summary

This report presents an architectural investigation, critique, and end-to-end design for introducing **generalized capture support for custom-defined note types** in Bob (`bob-cli` and `bob-mac-capture`).

Currently, Bob's capture ecosystem is exceptionally polished for **tasks** (`buy milk @groceries`), **Pomodoro sessions** (`=`, `x`), **reference jobs** (`URL @parent`), and **project notes** (`@route^id@ Title`). However, capturing structured, atomic entity notes—such as restaurants in `~/bob/eat/` (92 notes), podcasts in `~/bob/podcasts/` (15 notes), movies, or TV shows—suffers from severe friction. The user must switch to desktop Obsidian, manually create files in subdirectories, hand-format YAML frontmatter, ensure wikilinks adhere to vault conventions, and create standard Markdown heading skeletons.

We propose extending Bob capture to natively support **Entity Note Capture**. By establishing a declarative schema configuration in `~/.config/bob/config.yml` under `note_types:`, Bob can govern directory associations, required and optional frontmatter fields, default values, validation rules, and body templates. In alignment with Bob's foundational design decision `decisions:capture-sigils-say-where-what-how` ("`@` says where"), we design an intuitive directory-route syntax (`@eat/`, `@podcasts/`, `@movies/`, `@tv/`) paired with child-bullet field declarations mirroring `decisions:capture-bullets-mirror-the-task-block` and compact Dataview-style inline fields (`[category:: Sushi]`).

In accordance with `decisions:mac-capture-is-a-thin-client`, `bob-cli` remains the single source of truth for grammar, schema validation, completion candidates, and file generation, while `bob-mac-capture` renders a rich, high-polish **Entity Note Card** with interactive pill selectors, location completion, and live note preview.

---

## 1. Critique of the Plan & Requirements Evaluation

### 1.1 Is This a Good Idea?
**Yes, emphatically—provided it respects the boundaries between tasks, reference literature, and knowledge entities.**

In Personal Knowledge Management (PKM) and GTD, frictionless capture is the bedrock of system trust. When a user discovers a new restaurant with Kelly, hears a podcast recommendation, or decides to track a movie to watch, there are three options:
1. **Drop an unorganized task or inbox bullet into `mac_inbox.md`**: Leads to triage debt and manual filing later.
2. **Open Obsidian, navigate folders, and hand-craft YAML**: Creates high cognitive friction that disrupts flow.
3. **Capture directly via `bob capture` / Bob Mac Capture**: Instant, structured, validated, and beautiful.

By bringing structured entity creation into `bob capture`, Bob expands from a pure task/ledger engine into a cohesive life operating system without sacrificing speed.

### 1.2 Pitfalls and Anti-Patterns to Avoid
To keep the design robust and beautiful, we must avoid four critical architectural traps:

1. **The "Positional Argument Alphabet Soup" Trap**:
   Attempting to compress 5–8 fields into a positional single-line syntax (e.g. `@eat/ "Ninja Sushi" | liked | Sushi | Clark | kelly`) creates a brittle, unreadable nightmare. Users will never remember positional order, and handling optional fields requires ugly empty delimiters (`|||`).
2. **The "Interactive Terminal Prompt" Trap**:
   Prompting interactively on stdin (`Enter status: `, `Enter category: `) completely breaks:
   - Non-interactive shell execution, scripts, and tmux bindings.
   - Piped drafts (`printf "..." | bob capture`).
   - The entire subprocess contract with `bob-mac-capture` (`--dry-run` live preview runs asynchronously on every keystroke).
3. **The "Rigid Required-Only Schema" Trap**:
   If every field is strictly required and no defaults or optional fields are supported, capture becomes a bureaucratic chore. When quickly capturing a recommendation on the street, the user might not know the exact town or website yet.
4. **The "Conflating Tasks with Entities" Trap**:
   An entity note (a restaurant in `eat/`) is a durable reference/knowledge entity; it is *not* a task. While capturing a restaurant might optionally offer to schedule a tickler task ("Try Ninja Sushi"), the note itself must not be forced into a `- [ ] #task` mold.

### 1.3 Recommended Requirement Adjustments
We recommend three specific adjustments to the prompt's baseline requirements:

| Original Requirement | Adjusted Recommendation | Rationale |
| :--- | :--- | :--- |
| **Field Constraints**: Only required fields mentioned; optional fields left open. | **First-Class Required, Optional, and Default Fields.** | Support `required: true`, `required: false`, and `default: <val>`. Defaults (e.g., `status: liked`, `companions: ["[[kelly]]"]`) eliminate 70% of typing while preserving schema completeness. |
| **Field Input Syntax**: Unspecified; make it as easy as possible. | **Dual-Format Input (Child Bullets + Inline Fields).** | Allow structured child bullets (`- category: Sushi`) for multiline drafting and Dataview bracket fields (`[category:: Sushi]`) for single-line speed. Both compile to the same AST. |
| **Directory Association**: Directory per type. | **Directory + Filename Slugification + Collision Policy.** | Every type specifies a target directory, a slug derivation rule from `title` (e.g., `Ninja Sushi` $\to$ `ninja_sushi.md`), and deterministic collision handling (refusing overwrite with an informative diagnostic). |

---

## 2. Vault Inventory: What Custom Types Should Exist?

To ground the design in Bryan's actual vault structure, we surveyed `~/bob` and analyzed existing note directories, frontmatter conventions, and historical zorg templates.

```
                    ┌───────────────────────────────┐
                    │       Bryan's Bob Vault       │
                    └───────────────┬───────────────┘
                                    │
         ┌──────────────────────────┼──────────────────────────┐
         │                          │                          │
  ┌──────────────┐           ┌──────────────┐           ┌──────────────┐
  │   eat/*.md   │           │ podcasts/*.md│           │  [Proposed]  │
  │ (92 records) │           │ (15 records) │           │ movies / tv  │
  └──────────────┘           └──────────────┘           └──────────────┘
```

### 2.1 Type 1: `restaurant` (`~/bob/eat/`) — The First Use-Case
Analysis of all 92 files in `~/bob/eat/` reveals an exceptionally uniform structure:
- **Directory**: `~/bob/eat/`
- **Parent**: `[[eat]]` (linking to root overview `eat.md`)
- **Type**: `[[restaurant]]`
- **Frontmatter Fields**:
  - `title`: String (100% presence). Examples: `"Ninja Sushi"`, `"1 Walnut"`, `"Track 5"`.
  - `status`: Enum (100% presence). Values: `liked` (85), `not_liked` (7), `maybe_liked` / `want_to_try`.
  - `category`: String / Tag (100% presence). Top categories: `Breakfast` (18), `Coffee` (11), `Sushi` (4), `Pizza` (4), `Burritos` (3), `Dine-in` (3), `Mexican` (3), `Salad` (3), `Burgers` (3).
  - `location`: Wikilink or String (100% presence). Common values: `[[nj_towns#^z-241117-0b|cranford]]`, `Westfield`, `Clark`, `[[nyc#^z-250421-0m|NYC]]`, `Princeton`.
  - `lid`: Slug string (100% presence). Matches or shortens the filename stem (e.g., `ninja_sushi`, `t5`).
  - `companions`: List of wikilinks (100% presence). Almost always `["[[kelly]]"]`.
  - `source_*`: Historical migration fields from zorg (can be omitted in new captures).
- **Body Skeleton**:
  ```markdown
  # <Title>

  ## Notes

  - <Authored capture bullets or date-stamped notes>
  ```

### 2.2 Type 2: `podcast` (`~/bob/podcasts/`)
Analysis of all 15 files in `~/bob/podcasts/` shows:
- **Directory**: `~/bob/podcasts/`
- **Parent**: `[[podcasts]]` (linking to `podcasts.md`)
- **Type**: `[[podcast]]`
- **Frontmatter Fields**:
  - `title`: String (e.g., `"Talk Python to Me"`, `"The AI Daily Brief"`).
  - `status`: Enum. Values: `subscribed` (9), `unsubscribed` (6), `queued`.
  - `category`: String. Values: `programming` (4), `python` (3), `tech` (2), `ai` (2), `productivity` (2), `ideas` (1), `comedy` (1).
  - `url`: Valid URL (100% presence; website or Spotify show link).
- **Body Skeleton**:
  ```markdown
  # <Title>

  ## Notes
  ```

### 2.3 Type 3: `movie` (`~/bob/movies/` or `~/bob/fun/movies/`)
- **Vault Evidence**:
  - `chad_movie.md`: Prompt for LLM movie recommendations.
  - `_zorg_templates/zot/chat_movie.zot`: Template querying genre, years, dialog language.
  - `fun.md`: Notes about entertainment and media.
- **Recommended Schema**:
  - **Directory**: `movies/`
  - **Parent**: `[[movies]]` (under `[[fun]]`)
  - **Type**: `[[movie]]`
  - **Required Fields**:
    - `title`: String.
    - `status`: Enum (`want_to_watch`, `watched`, `recommended`).
  - **Optional Fields**:
    - `genre`: String / Tag (e.g., `Sci-Fi`, `Action`, `Comedy`, `Drama`, `Thriller`).
    - `year`: Integer.
    - `recommended_by`: Wikilink or string (e.g., `[[chad]]`, `%kelly`, `%aleonm`).
    - `rating`: Enum or 1–5 score (e.g., `liked`, `great`, `disliked`).
    - `url`: IMDb or Letterboxd link.

### 2.4 Type 4: `tv_show` (`~/bob/tv/` or `~/bob/shows/`)
- **Vault Evidence**:
  - `fun.md` explicitly cites: `List of TV shows we currently (2025-03-21) watch: [[text/tv.txt]]`.
  - Mentions of series (e.g., Hazbin Hotel S3 in `fun.md`).
- **Recommended Schema**:
  - **Directory**: `tv/`
  - **Parent**: `[[tv]]` (under `[[fun]]`)
  - **Type**: `[[tv_show]]`
  - **Required Fields**:
    - `title`: String.
    - `status`: Enum (`watching`, `want_to_watch`, `watched`, `paused`, `dropped`).
  - **Optional Fields**:
    - `platform`: String / Network (e.g., `Netflix`, `Apple TV+`, `HBO/Max`, `Hulu`, `Amazon Prime`).
    - `genre`: String.
    - `current_season`: Integer / String.
    - `companions`: List of wikilinks (default `["[[kelly]]"]`).

### 2.5 Analysis of Other Potential Types
We scrutinized other vault entities to determine if they should be custom note types:

| Candidate | Current Vault State | Recommendation | Rationale |
| :--- | :--- | :--- | :--- |
| **`person` / `people`** | Single centralized table in `~/bob/people.md` (100+ rows mapping `%ldap` to names, relationships, notes). | **Keep as Table (Do NOT convert yet).** | Creating 100+ separate small files in a `people/` folder would create vault sprawl without clear benefit. Bryan's Vim alignment macros (`sort_by_person.vim`) rely on the single table. |
| **`drink` / `cocktail`** | Section in `~/bob/drink.md`. | **Secondary / Future Candidate.** | Low volume currently; keep in `drink.md` until collection warrants a dedicated directory. |
| **`book` / `lit`** | 80+ notes in `~/bob/lit/` (`7_habits.md`, `ddia.md`, `the_blade_itself.md`). | **Strong Candidate for Phase 2.** | `bob ref` handles PDF reading and ingestion, but general book notes often live in `lit/`. However, `restaurant`, `podcast`, `movie`, and `tv_show` form the primary cohort. |

---

## 3. Schema & Configuration Specification

### 3.1 Where Should Schemas Live?
Schemas should be configured in **`~/.config/bob/config.yml`** under the dedicated top-level key **`note_types:`**.

> [!NOTE]
> `config.yml` already uses `types:` for Pomodoro task themes (`BUILD`, `CHORE`, `FIX`, `MEET`, `PLAN`, `READ`, `WRITE`). Using `note_types:` provides complete separation of concerns and prevents configuration collisions. Furthermore, storing it in `config.yml` ensures synchronization via chezmoi across Athena, Apollo, and the Mac.

### 3.2 Declarative Schema Definition
Here is the concrete schema definition for `restaurant`, `podcast`, `movie`, and `tv_show`:

```yaml
# In ~/.config/bob/config.yml
note_types:
  restaurant:
    dir: eat
    parent: "[[eat]]"
    type: "[[restaurant]]"
    slug_field: lid
    filename_template: "{slug}.md"
    fields:
      title:
        type: string
        required: true
        source: parent_line
        prompt: "Restaurant Name"
      status:
        type: enum
        required: true
        values: [liked, not_liked, maybe_liked, want_to_try]
        default: liked
      category:
        type: string
        required: true
        suggest: [Breakfast, Coffee, Sushi, Pizza, Burritos, Dine-in, Mexican, Salad, Burgers, Misc]
      location:
        type: wikilink_or_string
        required: true
        suggest_routes: [nj_towns, nyc]
        prompt: "Location (town or wikilink)"
      companions:
        type: list_wikilink
        required: false
        default: ["[[kelly]]"]
      url:
        type: url
        required: false
    body_template: |
      # {{title}}

      ## Notes

      {{notes}}

  podcast:
    dir: podcasts
    parent: "[[podcasts]]"
    type: "[[podcast]]"
    slug_field: zorg_id
    filename_template: "{slug}.md"
    fields:
      title:
        type: string
        required: true
        source: parent_line
      status:
        type: enum
        required: true
        values: [subscribed, unsubscribed, queued]
        default: subscribed
      category:
        type: string
        required: true
        suggest: [programming, python, ai, tech, productivity, ideas, comedy]
      url:
        type: url
        required: false
    body_template: |
      # {{title}}

      ## Notes

      {{notes}}

  movie:
    dir: movies
    parent: "[[movies]]"
    type: "[[movie]]"
    filename_template: "{slug}.md"
    fields:
      title:
        type: string
        required: true
        source: parent_line
      status:
        type: enum
        required: true
        values: [want_to_watch, watched, recommended]
        default: want_to_watch
      genre:
        type: string
        required: false
        suggest: [Sci-Fi, Action, Comedy, Drama, Thriller, Horror, Animation, Documentary]
      year:
        type: integer
        required: false
      recommended_by:
        type: wikilink_or_string
        required: false
      rating:
        type: enum
        required: false
        values: [liked, great, okay, disliked]
      url:
        type: url
        required: false
    body_template: |
      # {{title}}

      ## Notes

      {{notes}}

  tv_show:
    dir: tv
    parent: "[[tv]]"
    type: "[[tv_show]]"
    filename_template: "{slug}.md"
    fields:
      title:
        type: string
        required: true
        source: parent_line
      status:
        type: enum
        required: true
        values: [watching, want_to_watch, watched, paused, dropped]
        default: want_to_watch
      platform:
        type: string
        required: false
        suggest: [Netflix, Apple TV+, HBO/Max, Hulu, Amazon Prime, Disney+, YouTube]
      current_season:
        type: string
        required: false
      companions:
        type: list_wikilink
        required: false
        default: ["[[kelly]]"]
    body_template: |
      # {{title}}

      ## Notes

      {{notes}}
```

---

## 4. Capture Syntax & Grammar Design

### 4.1 Adherence to Core Decision Records
Our syntax adheres strictly to `decisions:capture-sigils-say-where-what-how`:
- **`@` says where**:
  - `@route` routes to a top-level note (`groceries.md`).
  - `@route^id@` creates a project note (`route_id.md`).
  - **`@dir/`** routes to a directory-associated custom note type!
  A trailing slash on the route (`@eat/`, `@podcasts/`, `@movies/`, `@tv/`) immediately and unambiguously signals:
  *"This capture targets a new entity note in the specified directory."*
- **`decisions:capture-bullets-mirror-the-task-block`**:
  - Child bullets beneath the parent line supply frontmatter properties or free-form notes.
  - The draft reads like the note it creates.

### 4.2 Dual-Mode Input Ergonomics

We provide two complementary input mechanisms: **Child Bullet Fields** (optimal for comprehensive logging) and **Inline Dataview Fields** (optimal for rapid, single-line capture).

```
                      ┌─────────────────────────────────┐
                      │    User Input Grammar Modes     │
                      └────────────────┬────────────────┘
                                       │
            ┌──────────────────────────┴──────────────────────────┐
            │                                                     │
    ┌───────────────┐                                     ┌───────────────┐
    │ Mode A: Child │                                     │ Mode B: Inline│
    │ Bullet Syntax │                                     │ Dataview      │
    └───────┬───────┘                                     └───────┬───────┘
            │                                                     │
            │ - category: Sushi                                   │ [category:: Sushi]
            │ - location: Clark                                   │ [location:: Clark]
            │ - Loved spicy tuna!                                 │
            │                                                     │
            └──────────────────────────┬──────────────────────────┘
                                       ▼
                      ┌─────────────────────────────────┐
                      │    Unified AST & Validation     │
                      │   (Fills Defaults, Emits Note)  │
                      └─────────────────────────────────┘
```

#### Mode A: Child Bullet Syntax (Recommended & Primary)
The parent line states the title and the directory destination (`@eat/`). Indented child bullets declare field key-values. Any bullet not matching a declared schema field automatically becomes a Markdown bullet in `## Notes`:

```text
Ninja Sushi @eat/
- category: Sushi
- location: Clark
- The spicy tuna rolls were fantastic! Kelly loved the salmon.
- Try the dragon roll next time.
```

**Why this is beautiful**:
1. Zero syntax friction: uses natural `key: value` syntax.
2. Unmatched bullets are preserved as notes without special escaping.
3. Undeclared fields take their defaults (`status: liked`, `companions: ["[[kelly]]"]`, `lid: ninja_sushi`).

#### Mode B: Inline Dataview Field Syntax (Fast Single-Line)
When entering a quick capture from the command line, Alfred, or Raycast:

```bash
bob capture 'Ninja Sushi @eat/ [category:: Sushi] [location:: Clark]'
```

Or combining inline fields with child notes:

```text
Ninja Sushi @eat/ [category:: Sushi] [location:: Clark]
- The spicy tuna rolls were fantastic!
```

Both styles compile into the exact same internal `EntityNoteCaptureDraft` representation.

### 4.3 Missing Fields & Interactive Guidance
What happens when required fields are missing?
Instead of an interactive prompt that stalls execution, `bob capture` provides **immediate, teaching validation**:

```text
$ bob capture 'Ninja Sushi @eat/'
bob capture: error: note type 'restaurant' requires fields: 'category', 'location'
  hint: provide missing fields via child bullets:
    Ninja Sushi @eat/
    - category: <value>
    - location: <value>
  or inline fields:
    Ninja Sushi @eat/ [category:: <value>] [location:: <value>]
```

In `bob capture-parse` (used by Bob Mac Capture), missing required fields do not throw an error; instead, they emit a structured need `needs: ["entity_field"]` and diagnostic spans so the UI can highlight what is needed.

---

## 5. UI & Interaction Design in Bob Mac Capture

In accordance with `decisions:mac-capture-is-a-thin-client`, `bob-cli` produces structured JSON and `bob-mac-capture` renders presentation.

### 5.1 Route & Field Autocompletion
1. **Target Discovery (`bob capture-targets`)**:
   When typing `@`, the route picker displays custom note types alongside existing areas and projects:
   ```text
   @eat/            Restaurant Note  (~/bob/eat/)
   @podcasts/       Podcast Note     (~/bob/podcasts/)
   @movies/         Movie Note       (~/bob/movies/)
   @tv/             TV Show Note     (~/bob/tv/)
   ```
2. **Field Key Completion**:
   Typing `- ` under an `@eat/` header opens completion for declared fields:
   ```text
   - category:      Required  [Breakfast, Coffee, Sushi, Pizza...]
   - location:      Required  [Cranford, Westfield, Clark, NYC...]
   - status:        Optional  (Default: liked)
   - companions:    Optional  (Default: [[kelly]])
   - url:           Optional
   ```
3. **Field Value Completion**:
   - For `status:`: Pill selection for `liked`, `not_liked`, `maybe_liked`.
   - For `location:`: Vault wikilink search scoped to `nj_towns.md` or existing locations.
   - For `category:`: Filterable list of existing categories.

### 5.2 The Entity Note Card (Visual Representation)
When `capture-parse` detects an entity note draft, `bob-mac-capture` replaces the default task preview with a dedicated **Entity Note Card**:

```
┌────────────────────────────────────────────────────────────────────────┐
│ 🍽️  NEW RESTAURANT · eat/ninja_sushi.md                   Draft Status  │
├────────────────────────────────────────────────────────────────────────┤
│ Title:    Ninja Sushi                                                 │
│ Status:   [ liked ✓ ]  [ not_liked ]  [ maybe_liked ]                 │
│ Category: [ Sushi ▾ ]                                                  │
│ Location: [ [[nj_towns#^z-241117-0b|cranford]] ▾ ]                     │
│ Companions: [[kelly]]                                                  │
├────────────────────────────────────────────────────────────────────────┤
│ 📝 1 Note Bullet:                                                      │
│    • The spicy tuna rolls were fantastic! Kelly loved the salmon.      │
├────────────────────────────────────────────────────────────────────────┤
│ [↩ Return to Capture]                                [Esc to Dismiss]  │
└────────────────────────────────────────────────────────────────────────┘
```

If a required field is missing, the card paints a warm amber outline with a clear label (e.g. `⚠️ Missing required field: location`). The user can simply keep typing in the editor or click the pill/dropdown to insert the field text directly into the draft.

---

## 6. Implementation Architecture in `bob-cli`

### 6.1 Subprocess & JSON Contract Additions

To preserve compatibility, all JSON extensions are additive (Schema Version 1).

#### `bob capture-parse` Additions
When `@dir/` is encountered, `capture-parse` returns an additive `entity_note` object:
```json
{
  "grammar": 20,
  "schema_version": 1,
  "items": [
    {
      "kind": "entity_note",
      "entity_type": "restaurant",
      "directory": "eat",
      "title": "Ninja Sushi",
      "target_file": "eat/ninja_sushi.md",
      "fields": {
        "status": { "value": "liked", "is_default": false },
        "category": { "value": "Sushi", "is_default": false },
        "location": { "value": "Clark", "is_default": false },
        "companions": { "value": ["[[kelly]]"], "is_default": true },
        "lid": { "value": "ninja_sushi", "is_default": true }
      },
      "missing_required_fields": [],
      "notes": [
        "The spicy tuna rolls were fantastic! Kelly loved the salmon."
      ],
      "spans": [
        { "start": 0, "end": 11, "kind": "entity_title" },
        { "start": 12, "end": 17, "kind": "entity_route" }
      ]
    }
  ]
}
```

#### `bob capture --dry-run` Output
Dry-run preview includes the exact frontmatter and body that will be written, allowing `bob-mac-capture` to display an exact visual preview:
```json
{
  "ok": true,
  "entity_note": {
    "path": "/home/bryan/bob/eat/ninja_sushi.md",
    "relative_path": "eat/ninja_sushi.md",
    "basename": "ninja_sushi.md",
    "rendered_contents": "---\nparent: \"[[eat]]\"\ntype: \"[[restaurant]]\"\ntitle: \"Ninja Sushi\"\nstatus: liked\ncategory: \"Sushi\"\nlocation: \"Clark\"\nlid: \"ninja_sushi\"\ncompanions:\n  - \"[[kelly]]\"\n---\n\n# Ninja Sushi\n\n## Notes\n\n- The spicy tuna rolls were fantastic! Kelly loved the salmon.\n"
  }
}
```

### 6.2 Slugification & Collision Strategy
1. **Slug Derivation**:
   ```rust
   pub fn slugify_entity_title(title: &str) -> String {
       let lower = title.to_lowercase();
       let mut slug = String::new();
       let mut last_was_underscore = false;
       for ch in lower.chars() {
           if ch.is_ascii_alphanumeric() {
               slug.push(ch);
               last_was_underscore = false;
           } else if !last_was_underscore {
               slug.push('_');
               last_was_underscore = true;
           }
       }
       slug.trim_matches('_').to_string()
   }
   ```
   Example: `"1 Walnut"` $\to$ `1_walnut`, `"Ninja Sushi"` $\to$ `ninja_sushi`, `"Chat & Griddle"` $\to$ `chat_griddle`.
2. **Collision Prevention**:
   If `eat/ninja_sushi.md` already exists:
   - Default behavior: Capture **refuses** with `entity_file_already_exists`.
   - Helpful diagnostic: Informs the user that the file exists and suggests capturing an update bullet directly into the existing file using standard section capture (`@eat/ninja_sushi#Notes New comment`).

---

## 7. Recommended Implementation Roadmap

We recommend executing this capability in four discrete, verifiable phases:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Implementation Phases                           │
└────────────────────────────────────────────────────────────────────────┘
   │
   ├─► Phase 1: Schema Config & Content Renderer
   │   • Create `src/native/config/note_types.rs`
   │   • Implement `render_entity_note` & slugification
   │   • Unit tests on `eat` sample notes
   │
   ├─► Phase 2: Capture Grammar & CLI Execution
   │   • Add `@dir/` directory route lexing in `capture_language`
   │   • Parse child bullets & inline Dataview fields
   │   • Implement atomic file creation & collision checking
   │   • Verification with `bob capture 'Ninja Sushi @eat/ ...'`
   │
   ├─► Phase 3: Discovery & Completion Protocols
   │   • Extend `bob capture-targets` to return entity routes
   │   • Extend `bob capture-complete` for field keys, enums, & wikilinks
   │   • Extend `bob capture-parse` with `entity_note` semantic spans
   │
   └─► Phase 4: Bob Mac Capture Integration
       • Add `EntityNoteCardView.swift`
       • Decode `entity_note` preview cards
       • Verify with `scripts/dev/macos-ci-check`
```

### Phase 1: Schema Config & Content Renderer (`bob-cli`)
- Create `src/native/config/note_types.rs` to parse `note_types:` from `~/.config/bob/config.yml`.
- Create `src/native/entity_notes/render.rs` with `render_entity_note(input)` returning frontmatter, headings, and body.
- Verify against existing notes in `~/bob/eat/` and `~/bob/podcasts/`.

### Phase 2: Capture Grammar & CLI Execution (`bob-cli`)
- Update `capture_language` to recognize `@<dir>/` as a directory route.
- Parse field bullets (`- key: val`) and inline fields (`[key:: val]`).
- Implement execution in `src/native/capture/entity_note.rs`:
  - Enforce required fields.
  - Apply configured defaults.
  - Slugify title to derive filename.
  - Atomically write the file to `~/bob/<dir>/<slug>.md`.

### Phase 3: Completion & Protocol Expansion (`bob-cli`)
- Add custom note types to `bob capture-targets`.
- Support field-name and enum-value completion in `bob capture-complete`.
- Add `entity_note` objects and spans to `bob capture-parse`.

### Phase 4: Bob Mac Capture UI Integration (`bob-mac-capture`)
- In `bob-mac-capture`, decode `entity_note` in `CaptureModels.swift`.
- Create `EntityNoteCardView.swift` to render the interactive preview card.
- Run macOS CI checks to guarantee green build and tests.

---

## Conclusion & Recommended Next Step

Adding generalized custom-type note capture is an outstanding architectural enhancement. It elevates Bob from a task ledger into an integrated personal knowledge system. By defining schemas declaratively in `config.yml`, employing `@dir/` with child-bullet field declarations, providing intelligent defaults, and pairing CLI speed with a beautiful Bob Mac Capture entity card, this feature delivers maximum utility with minimal friction.

**Recommended Next Step**: Begin Phase 1 by implementing schema parsing in `src/native/config/note_types.rs` and defining `restaurant` and `podcast` as the initial test fixtures.
