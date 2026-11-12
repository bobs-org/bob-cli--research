# Designing Obsidian Rendering and Modification UX for Album Record Schemas

**Author:** researcher `gem` (Independent Research Swarm)  
**Date:** 2026-11-12  
**Epic Context:** `bob-cli-k3` (Album notes — every record collection hangs under the area it serves)  
**Assigned Task:** Design an intuitive, reliable, and beautiful solution for rendering and modifying the `record` frontmatter field in Obsidian. Critique the premise, evaluate architectural alternatives, adjust requirements, and deliver a recommended implementation.

---

## 1. Executive Summary

In the `bob-cli-k3` architecture, record collection schemas (e.g., restaurants, podcasts, tv, movies) moved out of global configuration (`config.yml`) directly into the YAML frontmatter of their owner album notes (`eat.md`, `podcasts.md`, etc.) under the top-level `record:` key.

As captured in screenshot `~/tmp/screenshots/20261112_054646.png`, opening an album note like `eat.md` in Obsidian reveals a severe UX regression:
- Obsidian 1.4+ native **Properties** displays the `record` field with an unknown type icon (`[?]`).
- The entire multi-level YAML mapping is serialized into an unparsed, squished single-line JSON string:  
  `{"noun":"restaurant","label":"Restaurant","dated_notes":true,"fields":{"status":{"r...`
- It is visually jarring, clipped, impossible to read, and dangerous to edit: clicking into the box and modifying text risks flattening or escaping the YAML, corrupting frontmatter, and breaking `bob` CLI's Rust parser (`serde_yaml`).

### The Core Critique
Attempting to make Obsidian's native Properties table directly render and edit a nested schema mapping *in-place* within the property grid is an **architectural anti-pattern**:
1. **Platform Constraint:** Obsidian's Properties engine supports only scalar primitives (`text`, `number`, `checkbox`, `date`, `datetime`, `link`) and flat string lists. Obsidian provides **no public API to register custom property types** or custom property cell editors.
2. **Data Hazard:** Obsidian's internal properties manager will serialize any modified value in an unknown property cell as a raw string. If a user or script alters the value inside that cell, Obsidian will write back a string (e.g. `record: '{"noun": ...}'`), destroying the YAML mapping and causing `bob albums check` to fail.
3. **Domain Mismatch:** `record:` is not a simple metadata property (like `parent: "[[body]]"` or `emoji: 🍽️`). It is a **domain schema contract** defining field types, validation rules, required constraints, suggestion behavior, and status enum choices. Squeezing a database schema definition into a 200px key-value table row produces a terrible user experience.
4. **Frequency Mismatch:** Schemas are authored at creation and modified rarely (during domain evolution), whereas album notes are browsed, searched, and captured into daily. An intrusive inline editor in Properties creates visual clutter and accidental edit hazards.

### The Recommended Solution: A Three-Tier System
Instead of fighting Obsidian's Properties table, we recommend a cohesive three-tier design:
1. **Frontmatter Property Treatment ("Smart Schema Pill"):**  
   Replace the ugly unparsed JSON in the native Properties table with a clean, read-only status pill (`🏷️ Restaurant (restaurant) · 5 fields · 3 statuses [Edit ⚙️]`). Native property inputs are suppressed so Obsidian cannot corrupt the underlying YAML mapping. Alternatively, allow scoping this property row to `display: none` via view CSS so Properties displays only clean note metadata.
2. **Note Surface Presentation (Album Header Schema Card):**  
   In both Reading View and Live Preview, render a theme-integrated, collapsible **Schema Card** in the Album Header (directly below the ancestry breadcrumb and above H1). This card displays the schema noun, label, dated-notes indicator, typed field chips (`date`, `url`, `text`, `choices`, `number`), required/suggest badges, and status choice pills with emojis (e.g., `🔖 To try`, `💚 Liked`, `🚫 Not liked`).
3. **Modification UX ("Album Schema Builder Modal"):**  
   Clicking `[Edit Schema]` (from the Property pill, Header Card, or Command Palette `Bob: Edit Album Schema`) launches a dedicated, visual **Schema Builder Modal** (`AlbumSchemaEditorModal extends Modal`). This modal provides a structured GUI to add/edit fields, configure types, manage choices and emojis, preview live YAML, and validate against `bob-cli`'s Rust schema rules before executing an atomic frontmatter write and debounced `bob albums sync`.

---

## 2. Forensic Analysis of the Current State

### 2.1 The Problem in Screenshot `20261112_054646.png`
The screenshot shows Obsidian displaying `eat.md` in Live Preview / Reading View:
- At the top, Obsidian's native Properties panel renders:
  - `parent`: `body` (internal link)
  - `type`: `album` (internal link)
  - `summary`: `Restaurants Kelly and I have tried, liked, or want to try.` (text)
  - `emoji`: `🍽️` (text)
  - `index_by`: `location` (text)
  - `created`: `2026-06-11T13:07:00-04:00` (date/time)
  - `record`: `{"noun":"restaurant","label":"Restaurant","dated_notes":true,"fields":{"status":{"r...` (unknown `[?]`)
- Below the Properties panel:
  - `# Restaurants`
  - Intro text teaching `Name @eat/` and linking `[[eat.base]]`.
  - Line 7: `Schema: bob records show restaurant` (a legacy placeholder teaching hint).
  - `## Records` with the generated `[!records]` callout showing 104 restaurants grouped by status and location.

### 2.2 The Underlying YAML on Disk
In the vault checkout (`gh:bobs-org/bob/eat.md`), the frontmatter is clean, standard block YAML:
```yaml
---
parent: "[[body]]"
type: "[[album]]"
summary: Restaurants Kelly and I have tried, liked, or want to try.
emoji: 🍽️
index_by: location
created: 2026-06-11T13:07:00-04:00
record:
  noun: restaurant
  label: Restaurant
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
    visited:
      values: date
    url:
      values: url
  legacy:
  - lid
  - source_*
---
```

### 2.3 Why Obsidian Collapses `record:`
1. **Obsidian's Metadata Engine:** Obsidian reads frontmatter via `js-yaml` and stores it in its in-memory `MetadataCache`.
2. **Properties Component:** When Obsidian 1.4+ introduced visual Properties, it mapped YAML types to a fixed set of property widgets:
   - String -> Text widget
   - Number -> Number widget
   - Boolean -> Checkbox widget
   - Array of strings -> Tags or List widget
   - ISO date string -> Date widget
3. **Fallback Behavior for Mappings:** When a property value is a JavaScript object / nested dictionary (like `record:`), Obsidian has no widget for it. It assigns the fallback type `unknown` (`[?]`) and converts the object to a JSON string using `JSON.stringify(val)`.
4. **Write-Back Corruption:** If a user clicks into that input box or triggers Obsidian's property change listener, Obsidian writes back the string value. Obsidian's `processFrontMatter` or internal YAML serializer writes `record: "{\"noun\": ...}"` instead of an indented YAML block.
5. **CLI Impact:** `bob-cli`'s parser (`src/native/albums/mod.rs:record_section`) extracts the slice of lines under `record:` and parses them with `serde_yaml::from_str`. If it receives a flattened JSON string or escaped string scalar, schema diagnostics fire (`RecordDiagnosticCode::InvalidYaml` or `album_schema_invalid`), rendering the album broken and refusing captures!

---

## 3. Critique of the Plan & Premise

### 3.1 Is making `record` render and edit directly inside Properties a good idea?
**No.** Striving to make Obsidian's native Properties table an interactive, inline schema editor is an antipattern for three critical reasons:

| Dimension | Native Properties Table Reality | Schema Requirements |
| :--- | :--- | :--- |
| **Data Hierarchy** | Flat, single-level key-value rows | Deeply nested tree (fields -> options -> enum values) |
| **Screen Real Estate** | Narrow table column (typically 180–300px) | Needs space for field names, types, flags, labels, emojis |
| **API Extensibility** | Zero public API for custom property types | Requires custom validation, type selection, dropdowns |
| **Data Safety** | Overwrites YAML on blur/change without schema AST | Must preserve strict YAML formatting, comments, and order |

### 3.2 Evaluation of the Prior Plan (`plan:202611/album_plugin_ui.md`)
In `album_plugin_ui.md`, phase `album-header` (under `bob-cli-k3.7.1.4`) specified:
> "Render a read-only schema card in declaration order, including field labels, kinds, list markers, required marks, and choice labels... Hide `.metadata-property[data-property-key="record"]` only within an album note's own surface."

**Critique of that prior plan:**
- **What it got right:** Hiding `.metadata-property[data-property-key="record"]` correctly identified that Obsidian's native Properties table cannot handle nested mappings. Placing a read-only schema card in the header recognized that the note body is where rich presentation belongs.
- **Where it fell short:** It treated the schema as **read-only**. It provided **no modification affordance whatsoever**. To modify an album schema under that plan, Bryan would have to:
  1. Open Obsidian settings or toggle the file into raw Source mode (losing Live Preview formatting across the entire document).
  2. Scroll into raw frontmatter.
  3. Hand-edit nested YAML spacing and indentation, risking indentation errors that fail `bob albums check`.
  4. Switch back to Live Preview.
- This friction explains why Bryan requested this research: users need to see the schema render properly *and* have an easy, intuitive, beautiful way to modify it.

### 3.3 Necessary Requirements Adjustments
We recommend clearly adjusting the requirements as follows:

1. **Clarify "Render Properly in Obsidian":**  
   "Render properly" must **not** mean forcing a complex nested form into Obsidian's 2-column Properties table. Instead, it means:
   - In the Properties table: Replace the raw JSON string with a compact, polished **Schema Summary Badge** (or cleanly suppress the row via CSS).
   - In the Note Document: Render a full, elegant **Schema Card** in the Album Header that visually showcases all fields, types, and choices.
2. **Define "Easy to Modify":**  
   "Easy to modify" must mean a **dedicated Schema Builder Modal / Drawer** with visual form controls, input validation, and an optional YAML source editor tab.
3. **Enforce Safety & Schema Validation:**  
   Any modification UI must enforce the validation rules in `src/native/records/schema.rs` *before* saving to disk, preventing syntax corruption and invalid field definitions.

---

## 4. Evaluation of Technical Approaches

We evaluated four distinct technical architectures for delivering this capability:

```
+---------------------------------------------------------------------------------------+
|                                    ARCHITECTURAL SPECTRUM                              |
+---------------------------------------------------------------------------------------+
| Approach 1: DOM Hijack in Properties                                                  |
|   Inject complex multi-input DOM directly into .metadata-property[data-property-key]  |
|   Status: REJECTED (High fragility, race conditions, destructive serialization risks) |
+---------------------------------------------------------------------------------------+
| Approach 2: CLI-Only Schema Editing (`bob albums schema edit <stem>`)                 |
|   Terminal CLI commands or shell prompts outside Obsidian                             |
|   Status: REJECTED (Fails the "beautiful, intuitive in Obsidian" requirement)          |
+---------------------------------------------------------------------------------------+
| Approach 3: Source-Mode Frontmatter Jumper                                            |
|   Button jumps cursor to frontmatter in Source Mode                                   |
|   Status: INSUFFICIENT (Does not solve UI presentation; requires manual YAML typing)  |
+---------------------------------------------------------------------------------------+
| Approach 4: The Three-Tier Solution (RECOMMENDED)                                     |
|   1. Safe Property Pill in Properties table (prevents JSON dump & corruption)         |
|   2. Collapsible Schema Card in Album Header (Reading & Live Preview)                 |
|   3. Visual Schema Builder Modal with validation & YAML toggle                        |
|   Status: RECOMMENDED (Beautiful, 100% reliable, zero risk to vault data)             |
+---------------------------------------------------------------------------------------+
```

### Detailed Trade-Off Matrix

| Criteria | Approach 1: Properties DOM Hijack | Approach 2: CLI Commands | Approach 3: Source Jump | Approach 4: Recommended 3-Tier |
| :--- | :--- | :--- | :--- | :--- |
| **Visual Aesthetics** | Poor (cramped 200px cell) | None (terminal only) | Low (raw text) | **Exceptional** (Theme-native card & modal) |
| **Intuitive for User** | Low (awkward nested clicks) | Moderate (CLI commands) | Low (requires YAML syntax) | **High** (GUI builder with field types) |
| **Data Safety & Integrity** | **Dangerous** (Obsidian overwrite) | High (Rust validation) | Moderate (human error) | **High** (Pre-save validation & AST write) |
| **Maintenance Cost** | **High** (breaks on Obsidian DOM updates)| Low | Very low | Moderate (standard Obsidian Modal API) |
| **Live Preview & Reading** | Unstable | N/A | Disruptive | **Seamless** (identical across both views) |

---

## 5. Detailed Design: The Recommended Solution

The recommended solution consists of three complementary components in `bob-ledger-tools`:

```
+--------------------------------------------------------------------------------------+
|                                     EAT.MD IN OBSIDIAN                               |
+--------------------------------------------------------------------------------------+
|  PROPERTIES PANEL                                                                    |
|    parent:     body                                                                  |
|    type:       album                                                                 |
|    summary:    Restaurants Kelly and I have tried, liked, or want to try.            |
|    emoji:      🍽️                                                                    |
|    index_by:   location                                                              |
|    created:    2026-06-11T13:07:00-04:00                                             |
|    record:     [ 🏷️ restaurant · 5 fields · 3 statuses       [Edit ⚙️] ]  <-- Tier 1   |
+--------------------------------------------------------------------------------------+
|                                                                                      |
|  ALBUM HEADER                                                                        |
|  Body › Restaurants                                                  [＋ restaurant] |
|                                                                                      |
|  ▼ ⚙️ Schema: Restaurant (noun: restaurant)                         [⚙️ Edit Schema] |
|    Dated notes: Yes  ·  Index by: location  ·  Facets: default           <-- Tier 2   |
|    +------------------------------------------------------------------------------+  |
|    | Field     | Type     | Attributes           | Values / Choices               |  |
|    +-----------+----------+----------------------+--------------------------------+  |
|    | status    | choices  | required             | 🔖 To try · 💚 Liked · 🚫 Not  |  |
|    | category  | text     | required · suggest   |                                |  |
|    | location  | text     | required · suggest   |                                |  |
|    | visited   | date     | optional             |                                |  |
|    | url       | url      | optional             |                                |  |
|    +------------------------------------------------------------------------------+  |
|                                                                                      |
|  # Restaurants                                                                       |
|  Restaurants Kelly and I have tried... Add one with Name @eat/.                      |
|                                                                                      |
|  ## Records                                                                          |
|  > [!records] 104 restaurants · 🔖 11 to try · 💚 86 liked · 🚫 7 not liked          |
+--------------------------------------------------------------------------------------+
```

### 5.1 Tier 1: Frontmatter Property Treatment ("Smart Schema Pill")
To resolve the ugly `{"noun":"restaurant",...}` JSON in the Properties table:

1. **DOM Interception:**
   In `bob-ledger-tools`, when an album note is active:
   - Identify `.metadata-property[data-property-key="record"]`.
   - Hide the native input element via CSS:
     ```css
     .is-album-note .metadata-property[data-property-key="record"] .metadata-property-value input,
     .is-album-note .metadata-property[data-property-key="record"] .metadata-property-value-text {
       display: none !important;
     }
     ```
   - Inject a custom pill container `.bob-album-record-pill` into the property value cell:
     - Icon: `🏷️` or album emoji (`🍽️`).
     - Text: `restaurant · 5 fields · 3 statuses`.
     - Action button: `[Edit ⚙️]` (styled as a subtle, clickable icon button).
2. **Event Shielding:**
   - Clicks on the pill or `[Edit ⚙️]` button stop propagation (`event.stopPropagation()`), preventing Obsidian's property manager from activating an editor input.
   - Clicking opens the **Album Schema Builder Modal** (Tier 3).
3. **Clean Fallback Option:**
   Provide a setting in `Bob Ledger Tools`:
   - `Display record schema in Properties`: `Smart Pill` (default) vs `Hide Row`.
   - If `Hide Row` is selected, `.metadata-property[data-property-key="record"] { display: none; }` is applied, giving the user a completely pristine Properties table containing only note-level scalar properties.

### 5.2 Tier 2: Note Surface Presentation (Album Header Schema Card)
In both Reading View (via Markdown Post Processor) and Live Preview (via CodeMirror 6 ViewPlugin), render the **Album Header Schema Card** directly above `# <Title>`:

1. **Card Structure:**
   - **Header Bar:**
     - Left: Collapsible toggle chevron (`▼` / `▶`) + `⚙️ Schema: <Label>` + `(noun: <noun>)`.
     - Right: Action button `[⚙️ Edit Schema]` + `[＋ Add Field]`.
   - **Summary Row:**
     - `Dated notes:` Enabled / Disabled pill.
     - `Index by:` Field name pill (e.g. `location`).
     - `Facets:` Active facet fields (e.g. `category`).
   - **Field Grid / Table:**
     - Columns: `Field Name`, `Kind`, `Constraints`, `Allowed Values / Choices`.
     - `status`: Type badge `Choices`, `Required` badge, Choice chips displaying emojis and labels: `🔖 To try`, `💚 Liked`, `🚫 Not liked`.
     - `category`: Type badge `Text`, `Required` badge, `Suggest` badge.
     - `location`: Type badge `Text`, `Required` badge, `Suggest` badge.
     - `visited`: Type badge `Date`.
     - `url`: Type badge `URL`.
2. **Behavior & State:**
   - Collapsible state is stored in plugin view state (starts collapsed or expanded based on user preference, default: collapsed after initial review to minimize vertical bulk, or compact 1-line chip row that expands on click).
   - Data source: Reads directly from the cached `AlbumReport` (`bob albums list -f json`), which is already loaded by `bob-ledger-tools`'s album data service. Zero subprocess overhead at render time.

### 5.3 Tier 3: Modification UX ("Album Schema Builder Modal")
Clicking `[⚙️ Edit Schema]` or invoking `Bob: Edit Album Schema` from the Command Palette opens `AlbumSchemaEditorModal`:

```
+-------------------------------------------------------------------------------------+
|  Edit Schema: Restaurants (eat.md)                                            [ X ] |
+-------------------------------------------------------------------------------------+
|  [ Visual Builder ]  [ YAML Source ]                                                |
+-------------------------------------------------------------------------------------+
|  GENERAL SETTINGS                                                                   |
|  Noun:        [ restaurant         ]   Label:    [ Restaurant       ]               |
|  Plural:      [ restaurants        ]   Emoji:    [ 🍽️               ]               |
|  [x] Dated Notes (store visit/activity dates in record notes)                       |
|  Index By:    [ location      ▼ ]                                                   |
+-------------------------------------------------------------------------------------+
|  FIELDS (5 declared)                                               [ ＋ Add Field ] |
|                                                                                     |
|  ::: status (choices) · Required                                           [Edit] [x]|
|      Choices: to_try (🔖 To try), liked (💚 Liked), not_liked (🚫 Not liked)         |
|                                                                                     |
|  ::: category (text) · Required · Suggest                                  [Edit] [x]|
|                                                                                     |
|  ::: location (text) · Required · Suggest                                  [Edit] [x]|
|                                                                                     |
|  ::: visited (date)                                                        [Edit] [x]|
|                                                                                     |
|  ::: url (url)                                                             [Edit] [x]|
+-------------------------------------------------------------------------------------+
|  (!) Live Validation: Schema is valid.                                              |
|  Note: Modifying field keys does not rewrite existing records in eat/.              |
+-------------------------------------------------------------------------------------+
|  [ Cancel ]                                                  [ Save Schema Changes ]|
+-------------------------------------------------------------------------------------+
```

#### Detailed Modal Specifications:
1. **Dual Modes (Visual Builder & YAML Source):**
   - **Visual Builder Tab:** Intuitive, form-based editing for everyday adjustments (adding a field, adding a status choice, toggling required/suggest).
   - **YAML Source Tab:** Embedded CodeMirror editor showing the exact `record:` block with YAML syntax highlighting. Ideal for pasting schemas or making bulk edits. Both tabs stay synchronized in real time.
2. **Interactive Field Editor (Sub-panel or Inline Accordion):**
   - When adding or editing a field:
     - **Field Key:** Sanitized string (`[a-z0-9_]+`). Instant validation against reserved names: `parent`, `type`, `title`, `created`.
     - **Kind Selector:** Dropdown: `Text`, `Choices`, `Date`, `Link`, `Url`, `Number`.
     - **Flags:** Checkboxes for `Required`, `Suggest`, `List`.
     - **If Choices selected:** An interactive list of key-value pairs with emoji picker support:
       - Choice key (`to_try`) -> Label (`🔖 To try`).
       - Reorder handles, Add Choice button.
     - **If Number selected:** Numeric inputs for `Min` and `Max`.
3. **Safety & Validation Engine:**
   - Mirrors the exact validation logic from `src/native/records/schema.rs`:
     - Disallows reserved record IDs and field names.
     - Validates that choice values are non-empty.
     - Validates number bounds (`min <= max`).
     - Disallows duplicate field names.
   - If validation fails, the `[ Save Schema Changes ]` button is disabled, and an inline callout explains the issue with line/field context.
4. **Atomic Write & Synchronization:**
   - On Save:
     1. Uses Obsidian's `vault.process(file, ...)` to perform an atomic write to the note.
     2. Serializes the `record:` block using canonical 2-space indentation and exact key ordering (`noun`, `label`, `plural`, `dated_notes`, `fields`, `legacy`).
     3. Preserves all other frontmatter fields (`parent`, `type`, `summary`, `emoji`, `created`, `index_by`) untouched.
     4. Triggers `bob albums sync` (which `bob-ledger-tools` debounces).
     5. Shows a native Obsidian `Notice("Album schema updated successfully.")`.

---

## 6. Technical Implementation Breakdown in `bob-plugins`

All plugin changes belong in `plugins/bob-ledger-tools/src/` within the linked repository `bob-plugins`.

### 6.1 New and Modified Fragments
To comply with the repository rule that fragments remain below 1000 lines:

1. **`241n-plugin-album-header-schema.js` (~350 lines):**
   - Builds the DOM for the Album Header Schema Card.
   - Extracts field definitions, badges, constraints, and choices from the album report data.
   - Handles expand/collapse toggle and attaches the `[⚙️ Edit Schema]` button handler.
2. **`241p-plugin-album-property-pill.js` (~200 lines):**
   - Targets `.metadata-property[data-property-key="record"]`.
   - Injects the `.bob-album-record-pill` and suppresses native text inputs.
   - Connects click events to the modal launcher.
3. **`241q-album-schema-modal-model.js` (~400 lines):**
   - Pure, testable JavaScript data model.
   - Parses the `record:` frontmatter mapping into a mutable schema model.
   - Validates schema against `bob-cli` rules (`valid_identifier`, reserved keys, choice syntax).
   - Serializes the updated model back into canonical YAML.
4. **`241r-plugin-album-schema-modal.js` (~650 lines):**
   - Extends Obsidian's `Modal`.
   - Renders the General Settings, Field List, Field Edit dialog, and YAML Source toggle.
   - Manages atomic save via `app.vault.process(file)`.
5. **`styles.css`:**
   - Styling for `.bob-album-record-pill`, `.bob-album-schema-card`, and `.bob-schema-modal`.
   - Utilizes standard Obsidian CSS variables (`--interactive-accent`, `--background-secondary`, `--text-muted`, `--pill-radius`) to ensure flawless rendering across light and dark themes.

### 6.2 Test Coverage Strategy
Following `bob-plugins` testing standards:
- **Unit Tests:** Test `241q-album-schema-modal-model.js` in isolation:
  - Parsing real schemas from `eat.md`, `podcasts.md`, `tv.md`, `movies.md`.
  - Rejection of reserved field names (`parent`, `title`).
  - Validation of choice formatting and number bounds.
  - Byte-exact round-trip serialization of existing album schemas.
- **DOM Integration Tests:** Test `241n` and `241p`:
  - Verify pill injection in mock Properties DOM.
  - Verify event bubbling suppression.
  - Verify Schema Card rendering in Reading and Live Preview mock DOMs.

---

## 7. Edge Cases, Risks & Mitigations

1. **Destructive Changes to Existing Records:**
   - *Risk:* Renaming or deleting a field (e.g. removing `category` from `eat.md`) causes all 104 existing restaurant notes to fail `bob records check`.
   - *Mitigation:* The Schema Builder Modal detects field deletions and renames, displaying a prominent warning callout:  
     `"Warning: Existing records in eat/ use this field. Removing or renaming it will cause bob records check to report errors until records are migrated."`
2. **YAML Comment Preservation:**
   - *Risk:* Hand-authored YAML comments inside the `record:` block could be stripped by automated serializers.
   - *Mitigation:* `241q-album-schema-modal-model.js` uses an AST-preserving YAML parser (or targets line replacements), preserving top-level comments outside the modified keys.
3. **Obsidian Properties DOM Rerendering:**
   - *Risk:* Obsidian frequently tears down and rebuilds `.metadata-properties` during file navigation or focus changes.
   - *Mitigation:* Use idempotent decoration / MutationObserver checks. The pill injection checks if `.bob-album-record-pill` is already attached; if missing, it re-attaches cleanly without memory leaks.
4. **Source Mode Compatibility:**
   - *Risk:* Modifying frontmatter presentation interferes with power users in raw Source mode.
   - *Mitigation:* None of these decorations touch Source Mode. In Source Mode, Obsidian displays raw text, where users can type YAML as always.

---

## 8. Synthesis & Recommended Action Plan

### Recommended Plan of Record
1. **Adjust the Epic Scope in `bob-cli-k3.7.1`:**
   - Update `plan:202611/album_plugin_ui.md` under phase `album-header` (`bob-cli-k3.7.1.4`) or add a focused child phase `album-schema-modal`.
   - Confirm that the `record` property in Properties is treated with the **Smart Schema Pill** (or hidden via CSS), never exposed as a raw unparsed text box.
2. **Implement Phase 1 (Visual Presentation):**
   - Ship the **Smart Schema Pill** in Properties and the **Album Header Schema Card** in `bob-ledger-tools`.
   - Result: Screenshot `20261112_054646.png`'s ugly JSON string is immediately replaced with a beautiful, themed summary pill and header card.
3. **Implement Phase 2 (Modification UX):**
   - Ship `AlbumSchemaEditorModal` with the visual field builder, live validation, and YAML source toggle.
   - Wire the `[Edit Schema]` buttons and the `Bob: Edit Album Schema` command.
4. **Verify & Reconcile:**
   - Run `npm test` and `npm run docs:check` in `bob-plugins`.
   - Deploy with `bob plugins sync`.
   - Verify against real album notes (`eat.md`, `podcasts.md`, `tv.md`, `movies.md`) in Obsidian.

This design is intuitive (visual field builder), reliable (pre-save schema validation matching Rust rules), and beautiful (seamless Obsidian theme integration), completely eliminating the ugly raw JSON frontmatter artifact.
